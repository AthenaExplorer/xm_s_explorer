import datetime
import json, os

import django.db.transaction

from pro import jobs
from django.utils import timezone
from xm_s_common.decorator import common_ajax_response
from xm_s_common.utils import format_return, _d, format_price, format_power, VscodeBase, format_fil_to_decimal
from pro.interface import ProBase
from pro.prefix import MOBILE_PREFIX
from pro.serializers import *
from xm_s_common import inner_server
from xm_s_common.page import Page
from django.db.models.query_utils import Q


def check_pro_user(func):
    def _decorator(request, *args, **kwargs):
        # request.user_id= "b695624e1c3511ec84950242ac160050"
        if not request.user_id:
            return format_return(99905)
        pro_user, _ = ProBase.create_pro_user(request.user_id)
        if not pro_user or not pro_user.status:
            return format_return(16011)
        if not pro_user.is_pro or (pro_user.expire_time and pro_user.expire_time < timezone.now()):
            return format_return(16003, msg="专业版未激活或者已经到期")
        return func(request, *args, **kwargs)

    return _decorator


def check_user(func):
    def _decorator(request, *args, **kwargs):
        # request.user_id= "06f17060ba2611eba8e60242ac160045"
        if not request.user_id:
            return format_return(99905)
        pro_user, _ = ProBase.create_pro_user(request.user_id)
        if not pro_user or not pro_user.status:
            return format_return(16011)
        return func(request, *args, **kwargs)

    return _decorator


def _send_msg_code(mobile_prefix, mobile, method, content):
    """
    发送验证码
    :return:
    """
    if not mobile_prefix == "86":
        mobile = mobile_prefix+mobile
    vscode = VscodeBase(method=method, content=content)
    # 验证此手机号是否已经超过发送限制
    if not vscode.check_can_send_vercode(mobile):
        return format_return(11009)

    code = vscode.generate_code(mobile)
    if not code:
        return format_return(15000, msg="请勿频繁发送短信")
    content = vscode.content.format(code) + "【雅典娜浏览器】"
    print(content)
    # 发送手机验证码
    vscode.send_code(mobile, content)
    if os.getenv("DEVCODE", "dev") == "dev":
        return format_return(0, data=code)
    else:
        return format_return(0)


@common_ajax_response
def set_explorer_mobile(request):
    user_id = request.POST.get('user_id')
    mobile = request.POST.get('mobile')
    user = ProUser.objects.filter(user_id=user_id).first()
    if user:
        user.mobile = mobile
        user.save()
    return format_return(0)


@common_ajax_response
def invite_user(request):
    """邀请用户送PRO 注册用户送PRO"""
    user_id = request.POST.get('user_id')
    mobile = request.POST.get('mobile')
    invite_code = request.POST.get('invite_code')
    source = request.POST.get('source')
    # 被邀请
    if invite_code and ProUser.objects.filter(invite_code=invite_code).exists() \
            and not InviteRecord.objects.filter(user_id=user_id).exists():
        InviteRecord(invite_code=invite_code, user_id=user_id, mobile=mobile).save()
        ProBase.cal_invite_pro_time(invite_code)
    # 新注册送一个月PRO
    user, created = ProBase.create_pro_user(user_id)
    if user and source:
        user.source = source
        user.save()
    # if created and user and datetime.datetime.now() < datetime.datetime.strptime("2021-09-01", '%Y-%m-%d'):
    if created and user:
        user.expire_time = datetime.datetime.now() + datetime.timedelta(days=30)
        user.is_pro = True
        user.pro_tips_flag = True
        user.save()
    return format_return(0)


@common_ajax_response
@check_user
def update_pro_tips_flag(request):
    """更新PRO用户提醒标记位"""
    user_id = request.user_id
    ProUser.objects.filter(user_id=user_id).update(pro_tips_flag=False)
    return format_return(0)


@common_ajax_response
@check_pro_user
def get_pro_user_info(request):
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    pro_user = ProUser.objects.filter(user_id=user_id).first()
    if pro_user:
        data = ProUserModelSerializer(pro_user).data
        return format_return(0, data=data)
    else:
        return format_return(16003)


@common_ajax_response
@check_user
def get_pro_user(request):
    user_id = request.user_id
    pro_user = ProUser.objects.filter(user_id=user_id).first()
    if pro_user:
        data = ProUserModelSerializer(pro_user).data
        return format_return(0, data=data)
    else:
        return format_return(16003)


@common_ajax_response
@check_user
def get_collectible_miner(request):
    user_id = request.user_id
    objs = CollectibleMiner.objects.filter(user_id=user_id)
    data = CollectibleMinerModelSerializer(objs, many=True).data
    return format_return(0, data=data)


@common_ajax_response
@check_user
def add_collectible_miner(request):
    user_id = request.user_id
    miner_no = request.POST.get('miner_no')
    remarks = request.POST.get('remarks')
    obj = CollectibleMiner(user_id=user_id, miner_no=miner_no, remarks=remarks)
    obj.save()
    data = CollectibleMinerModelSerializer(obj).data
    return format_return(0, data=data)


@common_ajax_response
@check_user
def del_collectible_miner(request):
    user_id = request.user_id
    miner_no = request.POST.get('miner_no')
    obj = CollectibleMiner.objects.filter(user_id=user_id, miner_no=miner_no).first()
    if not obj:
        return format_return(99902, data=None, msg='无效的节点')
    obj.delete()
    return format_return(0, data=True)


@common_ajax_response
@check_user
def get_collectible_wallet_address(request):
    user_id = request.user_id
    objs = CollectibleWalletAddress.objects.filter(user_id=user_id)
    data = CollectibleWalletAddressModelSerializer(objs, many=True).data
    return format_return(0, data=data)


@common_ajax_response
@check_user
def add_collectible_wallet_address(request):
    user_id = request.user_id
    wallet_address = request.POST.get('wallet_address')
    remarks = request.POST.get('remarks')
    obj = CollectibleWalletAddress(user_id=user_id, wallet_address=wallet_address, remarks=remarks)
    obj.save()
    data = CollectibleWalletAddressModelSerializer(obj).data
    return format_return(0, data=data)


@common_ajax_response
@check_user
def del_collectible_wallet_address(request):
    user_id = request.user_id
    wallet_id = request.POST.get('wallet_id')
    wallet_address = request.POST.get('wallet_address')
    obj = CollectibleWalletAddress.objects.filter(Q(wallet_address=wallet_address) | Q(wallet_address=wallet_id),
                                                  user_id=user_id).first()
    if not obj:
        return format_return(99902, data=None, msg='无效的钱包地址')
    obj.delete()
    return format_return(0, data=True)


@common_ajax_response
@check_user
def get_collectible_miner_list(request):
    """"获取节点收藏排序"""
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    filter_type = request.POST.get('filter_type', "")  # raw_power:有效算力  power_inc：算力增速 avg_reward：产出效率
    sector_type = request.POST.get('sector_type')  # 0 是32G 1 是64G
    stats_type = request.POST.get('stats_type', '24h')  # 24h/7d/30d/90d
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)

    collectible_miners = ProBase.get_collectible_miners(user_id)
    miner_no_dict = {miner.miner_no: miner.remarks for miner in collectible_miners}
    if not miner_no_dict:
        return format_return(0, data={'objects': [], 'total_page': 0, 'total_count': 0})
    request_dict = {
        "sector_type": sector_type,
        "miner_no_list": json.dumps(list(miner_no_dict.keys())),
        "page_index": page_index,
        "page_size": page_size,
        "stats_type":stats_type
    }
    if filter_type == "raw_power":
        miner_rank_result = inner_server.get_miner_ranking_list_by_power(request_dict)
    if filter_type == "power_inc":
        request_dict["filter_type"] = "increase_power"
        miner_rank_result = inner_server.get_miner_ranking_list(request_dict)

    if filter_type == "avg_reward":
        request_dict["filter_type"] = filter_type
        miner_rank_result = inner_server.get_miner_ranking_list(request_dict)

    for miner_rank in miner_rank_result.get("data", {}).get("objects", []):
        miner_rank["remarks"] = miner_no_dict.get(miner_rank["miner_no"])
        miner_rank["flag"] = False
    return format_return(0, data=miner_rank_result.get("data"))


@common_ajax_response
@check_user
def get_collectible_address_list(request):
    """"获取账户收藏排序"""
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)

    collectible_wallet_address = ProBase.get_collectible_address(user_id)
    wallet_address_dict = {wallet.wallet_address: wallet.remarks for wallet in collectible_wallet_address}
    if not wallet_address_dict:
        return format_return(0, data={'objects': [], 'total_page': 0, 'total_count': 0})
    wallet_address_list = list(wallet_address_dict.keys())
    request_dict = {
        "id_address_list": json.dumps(wallet_address_list),
        "page_index": page_index,
        "page_size": page_size,
    }

    wallets_result = inner_server.get_wallets_list(request_dict)

    for wallets in wallets_result.get("data", {}).get("objects", []):
        wallets["remarks"] = wallet_address_dict.get(wallets["address"])
        wallets["flag"] = False

    return format_return(0, data=wallets_result.get("data"))


@common_ajax_response
@check_user
def get_collectible_status(request):
    """
    判断节点是否收藏
    :param request:
    :return:
    """
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    collectible_id = request.POST.get('collectible_id')
    collectible_type = request.POST.get('type', "miner")
    result = ProBase.get_collectible_status(user_id, collectible_id, collectible_type)
    return format_return(0, data=result)


@common_ajax_response
@check_user
def update_collectible(request):
    """
    更新收藏
    :param request:
    :return:
    """
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    collectible_id = request.POST.get('collectible_id')
    collectible_type = request.POST.get('type', "miner")
    remarks = request.POST.get('remarks')
    result = ProBase.update_collectible(user_id, collectible_id, collectible_type, remarks)
    if result:
        return format_return(0, data=result)
    return format_return(-1, data=result, msg="更新失败")


@common_ajax_response
@check_pro_user
def get_miner_monitor(request):
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    warn_method = request.POST.get('warn_method')
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    objs = MinerMonitor.objects.filter(user_id=user_id, warn_method=warn_method)
    data_result = Page(objs, page_size).page(page_index)
    data_result["objects"] = MinerMonitorModelSerializer(data_result["objects"], many=True).data
    return format_return(0, data=data_result)


@common_ajax_response
@check_pro_user
def create_update_miner_monitor(request):
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    miner_no = request.POST.get('miner_no')
    warn_method = request.POST.get('warn_method')
    warn_mobile_ids = json.loads(request.POST.get('warn_mobile_ids', "[]"))
    remarks = request.POST.get('remarks')
    wallet_type = request.POST.get('wallet_type')
    value = request.POST.get('value', "0")
    if warn_method in ["create_gas", "avg_reward", "sector_faulty"]:
        monitor_values = ProBase.get_miner_monitor_value(miner_no, warn_method)
        if not monitor_values:
            return format_return(16008, '节点或者钱包地址无效')
    elif warn_method in ["fil_change", "fil_balance"]:
        if not wallet_type:
            return format_return(16001, ' 参数错误')
        monitor_values = ProBase.get_wallet_address_value(miner_no, wallet_type)
        if not monitor_values:
            return format_return(16008, '节点或者钱包地址无效')
    else:
        return format_return(16001, ' 参数错误')
    warn_mobiles = WarnMobile.objects.filter(id__in=warn_mobile_ids, user_id=user_id).all()
    if not warn_mobiles:
        return format_return(16001, '手机号编号错误')
    obj, created = MinerMonitor.objects.get_or_create(miner_no=miner_no, user_id=user_id, warn_method=warn_method)
    obj.remarks = remarks
    obj.value = _d(value)
    obj.warn_mobiles.clear()
    obj.warn_mobiles.add(*warn_mobiles)
    for key, monitor_value in monitor_values.items():
        setattr(obj, key, monitor_value)
    obj.save()
    data = MinerMonitorModelSerializer(obj).data
    return format_return(0, data=data)


@common_ajax_response
@check_pro_user
def del_miner_monitor(request):
    oid = int(request.POST.get('id'))
    user_id = request.user_id
    obj = MinerMonitor.objects.filter(id=oid, user_id=user_id).first()
    if not obj:
        return format_return(99902, data=None, msg='无效的ID')
    obj.delete()
    return format_return(0, data=True)


@common_ajax_response
@check_pro_user
def get_warn_mobile(request):
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    objs = WarnMobile.objects.filter(user_id=user_id)
    data = WarnMobileModelSerializer(objs, many=True).data
    return format_return(0, data=data)


@common_ajax_response
@check_pro_user
@django.db.transaction.atomic
def del_warn_mobile(request):
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    oid = int(request.POST.get('id'))
    obj = WarnMobile.objects.filter(id=oid, user_id=user_id).first()
    if not obj:
        return format_return(99902, data=None, msg='无效的ID')
    pro_user = ProUser.objects.filter(user_id=user_id).first()
    if pro_user.mobile == obj.mobile:
        return format_return(99902, data=None, msg='登录手机号不支持删除！')
    miner_monitor_id = []  # 找出只有一个告警手机的数据然后删除
    for miner_monitor in obj.miner_monitors.all():
        if miner_monitor.warn_mobiles.filter(~Q(id=oid)).count() > 0:
           continue
        miner_monitor_id.append(miner_monitor.id)
    MinerMonitor.objects.filter(id__in=miner_monitor_id).delete()
    obj.delete()
    return format_return(0, data=True)


@common_ajax_response
@check_pro_user
def get_change_mobile_vercode(request):
    mobile = request.POST.get('mobile')
    mobile_prefix = request.POST.get('mobile_prefix', '86')
    if mobile_prefix not in [i['prefix'] for i in MOBILE_PREFIX]:
        return format_return(16005, "手机区号错误")
    content = "验证码{}，5分钟后失效。您正在进行监控手机操作，请勿泄露短信验证码"
    return _send_msg_code(mobile_prefix, mobile, "change_mobile", content)


@common_ajax_response
@check_pro_user
def add_warn_mobile(request):
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    mobile = request.POST.get('mobile')
    verification_code = request.POST.get('verification_code')
    if not mobile.isdigit():
        return format_return(16001, msg="手机号必须为纯数字")
    mobile_prefix = request.POST.get('mobile_prefix', '86')
    if mobile_prefix not in [i['prefix'] for i in MOBILE_PREFIX]:
        return format_return(16005, "手机区号错误")
    if WarnMobile.objects.filter(mobile=mobile, user_id=user_id):
        return format_return(16006, '手机号已存在')
    if not VscodeBase(method="change_mobile").ver_code(verification_code, mobile):
        return format_return(15000, "验证码错误")
    if WarnMobile.objects.filter(user_id=user_id).count() < 3:
        obj = WarnMobile(user_id=user_id, mobile=mobile, mobile_prefix=mobile_prefix)
        obj.save()
        data = WarnMobileModelSerializer(obj).data
        return format_return(0, data=data)
    else:
        return format_return(16007, '监控手机数量已达上限')


@common_ajax_response
@check_pro_user
def set_warn_mobile(request):
    user_id = request.user_id
    # user_id = "06f17060ba2611eba8e60242ac160045"
    mobile = request.POST.get('mobile')
    verification_code = request.POST.get('verification_code')
    if not mobile.isdigit():
        return format_return(16001, msg="手机号必须为纯数字")
    mobile_prefix = request.POST.get('mobile_prefix', '86')
    if mobile_prefix not in [i['prefix'] for i in MOBILE_PREFIX]:
        return format_return(16005, "手机区号错误")
    if WarnMobile.objects.filter(mobile=mobile, user_id=user_id):
        return format_return(16006, '手机号已存在')
    oid = request.POST.get('id')
    obj = WarnMobile.objects.filter(user_id=user_id, id=oid).first()
    if not obj:
        return format_return(16004, 'ID未找到')
    if not VscodeBase(method="change_mobile").ver_code(verification_code, mobile):
        return format_return(15000, "验证码错误")
    obj.mobile = mobile
    obj.mobile_prefix = mobile_prefix
    obj.save()
    data = WarnMobileModelSerializer(obj).data
    return format_return(0, data=data)


@common_ajax_response
@check_pro_user
def miner_health_report_24h(request):
    """"节点健康报告24H详情"""
    user_id = request.user_id
    miner_no = request.POST.get('miner_no')
    request_dict = {
        "miner_no": miner_no,
    }
    miner_result = inner_server.get_miner_health_report_24h_by_no(request_dict)
    return format_return(0, data=miner_result.get("data"))


@common_ajax_response
@check_pro_user
def miner_health_report_days(request):
    """"节点健康报告7天列表"""
    miner_no = request.POST.get('miner_no')
    request_dict = {
        "miner_no": miner_no,
    }
    miner_result = inner_server.get_miner_health_report_day_by_no(request_dict)

    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=7)
    request_dict = {
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": (end_date+datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    }
    # 全网值按天
    overview_result = inner_server.get_overview_day_list(request_dict)
    overview_dict = {overview["date"]: overview for overview in overview_result.get("data", {}).get("objects", [])}
    avg_reward_warn = True  # 连续7天节点的产出效率低于全网均值的80%
    create_gas_warn, keep_gas_warn = True, True  # 连续7天节点的生产Gas、维护Gsa高于全网均值的30%
    lucky_warn = False  # 连续7天节点的幸运值低于官方基准值的50 %
    is_32 = False
    for miner_day in miner_result.get("data", []):
        overview_tmp = overview_dict.get(miner_day["date"], {})
        miner_day["avg_reward_overview"] = overview_tmp.get("avg_reward", 0)
        avg_reward_warn &= _d(miner_day["avg_reward"]) < _d(miner_day["avg_reward_overview"]) * _d(1-0.8)

        is_32 = bool(miner_day["is_32"])
        miner_day["create_gas_overview"] = overview_tmp.get("create_gas_32", 0) \
            if is_32 else overview_tmp.get("create_gas_64")
        create_gas_warn &= _d(miner_day["create_gas"]) > _d(miner_day["create_gas_overview"]) * _d(1 + 0.3)
        miner_day["keep_gas_overview"] = overview_tmp.get("keep_gas_32", 0) \
            if is_32 else overview_tmp.get("keep_gas_64")
        keep_gas_warn &= _d(miner_day["keep_gas"]) > _d(miner_day["keep_gas_overview"]) * _d(1+0.3)

        miner_day["pledge"] = _d(overview_tmp.get("avg_pledge", 0))
        lucky_warn &= _d(miner_day["lucky"]) < _d(0.9970) * _d(0.5)
    gas_warn = create_gas_warn | keep_gas_warn
    # 成本评分
    gas_score = ProBase.get_score_content("CS2" if gas_warn else "CS1")[1]
    # 爆快（幸运评分）
    lucky_score = ProBase.get_score_content("W2" if lucky_warn else "W1")[1]
    return format_return(0, data=dict(objs=miner_result.get("data"), avg_reward_warn=avg_reward_warn,
                                      gas_warn=gas_warn, create_gas_warn=create_gas_warn, keep_gas_warn=keep_gas_warn,
                                      gas_score=gas_score, lucky_warn=lucky_warn, lucky_score=lucky_score, is_32=is_32))


@common_ajax_response
@check_pro_user
def miner_health_report_gas_stat(request):
    """"节点健康报告gas分析"""
    miner_no = request.POST.get('miner_no')
    stat_type = request.POST.get('stat_type')
    request_dict = {
        "miner_no": miner_no,
        "stat_type": stat_type
    }
    miner_result = inner_server.get_miner_health_report_gas_stat_by_no(request_dict)
    return format_return(0, data=miner_result.get("data"))


@common_ajax_response
@check_pro_user
def miner_health_report_messages_stat(request):
    """"节点健康报告消息分析"""
    user_id = request.user_id
    miner_no = request.POST.get('miner_no')
    stat_type = request.POST.get('stat_type')
    request_dict = {
        "miner_no": miner_no,
        "stat_type": stat_type
    }
    miner_result = inner_server.get_messages_stat_by_miner_no(request_dict)
    return format_return(0, data=miner_result.get("data"))


@common_ajax_response
@check_pro_user
def get_miner_health_report_stats(request):
    """"获取节点健康报告评分统计"""
    user_id = request.user_id
    miner_no = request.POST.get('miner_no')
    request_dict = {
        "miner_no": miner_no,
    }

    result_dict = inner_server.get_overview_stat().get("data", {})  # 全网概览
    if not result_dict:
        return format_return(0)
    overview_avg_reward = _d(result_dict.get("avg_reward"))  # 全网产出效率
    overview_pledge = _d(result_dict.get("avg_pledge"))  # 全网单T质押
    overview_create_gas_32 = _d(result_dict.get("create_gas_32"))  # 全网32生成成本
    overview_create_gas_64 = _d(result_dict.get("create_gas_64"))  # 全网单体质押
    overview_raw_power = _d(result_dict.get("power"))  # 全网总算力

    miner_result = inner_server.get_miner_by_miner_no(request_dict).get("data", {})
    if not miner_result:
        return format_return(0)
    miner_stats_result = inner_server.get_miner_stats_by_no(request_dict).get("data", {})
    if not miner_stats_result:
        return format_return(0)
    # 运行状态
    # 正常：扇区无错误，无掉算力情况
    # 良好：扇区错误，但没掉算力
    # 异常：有掉算力
    increase_power_offset_24 = miner_stats_result.get("increase_power_offset")
    faulty_sector = miner_result.get("sector_faults", 0)
    miner_power = _d(miner_result.get("actual_power", 0))
    status_score = "S1"
    if faulty_sector > 0 and _d(increase_power_offset_24) >= 0:
        status_score = "S2"
    if _d(increase_power_offset_24) < 0:
        status_score = "S3"
    status_dict = dict(
        faulty_sector=faulty_sector,
        increase_power_offset_24=format_power(increase_power_offset_24),
        score=ProBase.get_score_content(status_score)[1],
        status=ProBase.get_score_content(status_score)[0],
        mark=round(1 - miner_power / overview_raw_power, 2)
    )
    # 产出效率
    # 非常高效：高于全网均值30 %
    # 优秀：高于全网均值30 % 以内
    # 中等：低于全网均值30 %
    # 低效：低于全网均值30 % 以上
    avg_reward = _d(miner_stats_result.get("avg_reward", 0))
    avg_reward_dict = dict(
        avg_reward=avg_reward
    )
    avg_reward_score, avg_reward_dict["mark"] = ProBase.avg_reward_percentage_score(avg_reward, overview_avg_reward)
    avg_reward_dict["status"], avg_reward_dict["score"] = ProBase.get_score_content(avg_reward_score)

    miner_health_result = inner_server.get_miner_health_report_24h_by_no(request_dict).get("data", {})
    if not miner_health_result:
        return format_return(0)
    # 新增算力成本:生产成本+质押成本
    # 非常低：低于全网均值10 % 以上
    # 低：低于全网均值10 % 以内
    # 中等：高于全网均值10 % 以内
    # 高：高于全网均值10 % 以上
    create_gas = _d(miner_health_result.get("create_gas", 0))
    sector_size = miner_health_result.get("sector_size")
    cost = create_gas + overview_pledge
    overview_cost = (overview_create_gas_32 if sector_size == "32.00 GiB" else overview_create_gas_64) + overview_pledge
    cost_dict = dict(
        cost=cost, overview_cost=overview_cost
    )
    cost_score, cost_dict["mark"] = ProBase.cost_percentage_score(cost, overview_cost)
    cost_dict["status"], cost_dict["score"] = ProBase.get_score_content(cost_score)
    return format_return(0, data=dict(status_dict=status_dict, avg_reward_dict=avg_reward_dict, cost_dict=cost_dict))


@common_ajax_response
@check_pro_user
def miner_health_report_wallet_estimated_day(request):
    user_id = request.user_id
    miner_no = request.POST.get('miner_no')
    request_dict = {
        "miner_no": miner_no,
    }
    wallet_result = inner_server.get_wallet_address_estimated_service_day(request_dict).get("data", {})
    worker_estimated_day = int(wallet_result.get("worker_estimated_day", 0))
    poster_estimated_day = int(wallet_result.get("poster_estimated_day", 0))
    # 钱包状态
    worker_warn, poster_warn = True, True
    cost_score_list = ["WA1", "WA2"]
    if worker_estimated_day != -1 and worker_estimated_day <= 3:
        worker_warn &= False
        cost_score_list.remove("WA1")
    if poster_estimated_day != -1 and poster_estimated_day <= 3:
        poster_warn &= False
        cost_score_list.remove("WA2")
    wallet_score = sum([ProBase.get_score_content(cost_score)[1] for cost_score in cost_score_list])
    wallet_result["wallet_score"] = wallet_score
    wallet_result["worker_warn"] = worker_warn
    wallet_result["poster_warn"] = poster_warn
    wallet_result["wallet_warn"] = worker_warn | poster_warn
    return format_return(0, data=wallet_result)


@common_ajax_response
def sync_update_miner_monitor(request):
    now_date = datetime.datetime.today().date()
    monitor_values = {}
    for monitor in MinerMonitor.objects.filter(warn_method__in=["create_gas", "avg_reward", "fil_balance",
                                                                "sector_faulty"]).all():
        pro_user = ProUser.objects.filter(user_id=monitor.user_id).first()
        if not pro_user or not pro_user.status:
            continue
        if not pro_user.is_pro or (pro_user.expire_time and pro_user.expire_time < timezone.now()):
            continue
        if monitor.warn_method in ["create_gas", "avg_reward", "sector_faulty"]:
            monitor_values = ProBase.get_miner_monitor_value(monitor.miner_no, monitor.warn_method)
        if monitor.warn_method in ["fil_balance"]:
            monitor_values = ProBase.get_wallet_address_value(monitor.miner_no, monitor.wallet_type)
        for key, monitor_value in monitor_values.items():
            setattr(monitor, key, monitor_value)
        monitor.save()
        eval("jobs.send_{}_sms(monitor,now_date)".format(monitor.warn_method))
    return format_return(0)


@common_ajax_response
def sync_update_wallet_monitor(request):
    now_date = datetime.datetime.today().date()
    for monitor in MinerMonitor.objects.filter(warn_method="fil_change").all():
        pro_user = ProUser.objects.filter(user_id=monitor.user_id).first()
        if not pro_user or not pro_user.status:
            continue
        if not pro_user.is_pro or (pro_user.expire_time and pro_user.expire_time < timezone.now()):
            continue
        monitor_values = ProBase.get_wallet_address_value(monitor.miner_no, monitor.wallet_type)
        for key, monitor_value in monitor_values.items():
            setattr(monitor, key, monitor_value)
        monitor.save()
        eval("jobs.send_{}_sms(monitor,now_date)".format(monitor.warn_method))
    return format_return(0)


@common_ajax_response
@check_user
def get_invite_info(request):
    """
    获取邀请信息
    :param request:
    :return:
    """
    user_id = request.user_id
    # user_id ="06f17060ba2611eba8e60242ac160045"
    result = ProBase.get_invite_info(user_id)
    return format_return(0, data=result)


@common_ajax_response
@check_user
def get_invite_record_list(request):
    """
    获取邀请记录列表
    :param request:
    :return:
    """
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    user_id = request.user_id
    # user_id ="06f17060ba2611eba8e60242ac160045"
    user = ProUser.objects.filter(user_id=user_id).first()
    objs = InviteRecord.objects.filter(invite_code=user.invite_code)
    data_result = Page(objs, page_size).page(page_index)
    data_result["objects"] = InviteRecordModelSerializer(data_result["objects"], many=True).data
    return format_return(0, data=data_result)


@common_ajax_response
@check_user
def get_reward_record_list(request):
    """
    获取奖励记录列表
    :param request:
    :return:
    """
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    user_id = request.user_id
    # user_id ="06f17060ba2611eba8e60242ac160045"
    user = ProUser.objects.filter(user_id=user_id).first()
    objs = RewardRecord.objects.filter(invite_code=user.invite_code)
    data_result = Page(objs, page_size).page(page_index)
    data_result["objects"] = RewardRecordModelSerializer(data_result["objects"], many=True).data
    return format_return(0, data=data_result)

