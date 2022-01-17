import time,json,datetime
from django.db import transaction
from fad.interface import get_newest_fil_index
from master_overview.interface import OverViewBase
from master_overview.models import MinerApplyTag
from master_overview.serializer import MinerApplyTagSerializer, MinerTagQuerySerializer, \
    MinerApplyTagSetSerializer
from xm_s_common import inner_server
from xm_s_common.utils import format_return, format_coin_to_str, un_format_fil_to_decimal, format_float_coin, \
    prams_filter
from xm_s_common.decorator import common_ajax_response
from xm_s_common.utils import format_fil,format_power
from xm_s_common.third.binghe_chain_sdk import BingheChainBase
from exponent.models import MinerBase
from xm_s_common.third.filfox_sdk import FilfoxBase
from xm_s_common.page import Page
from admin.models import TagStatus


@common_ajax_response
def get_overview(request):
    result_dict = inner_server.get_net_ovewview().get("data")  # 概览
    result_dict['base_fee_format'] = format_float_coin(result_dict['base_fee'] if result_dict.get("base_fee") else 0)
    result_dict['base_fee'] = result_dict['base_fee'] if result_dict.get("base_fee") else 0
    result_dict['fil_index_objs'] = get_newest_fil_index()  # fil指数
    # 实时的gas消耗
    result_dict['real_time_gas'] = dict()
    real_time_64 = {'create_gas_str': format_float_coin(un_format_fil_to_decimal(
        result_dict.get('create_gas_64') if result_dict.get('create_gas_64') else 0), point=4)}  # 64g
    result_dict['real_time_gas']["gas_64"] = real_time_64
    real_time_32 = {'create_gas_str': format_float_coin(un_format_fil_to_decimal(
        result_dict.get('create_gas_32') if result_dict.get('create_gas_32') else 0), point=4)}  # 32g
    result_dict['real_time_gas']["gas_32"] = real_time_32

    # 历史24小时的数据
    query_dict_64 = {"sector_type": "1"}
    history_result_64 = inner_server.get_gas_cost_stat(query_dict_64).get("data")
    history_result_32 = inner_server.get_gas_cost_stat().get("data")
    history_time_gas = {
        "gas_64": {
            "create_gas_64": format_float_coin(un_format_fil_to_decimal(
                history_result_64['create_gas'] if history_result_64.get('create_gas') else 0), point=4),
            "keep_gas_64": format_float_coin(un_format_fil_to_decimal(
                history_result_64['keep_gas'] if history_result_64.get('keep_gas') else 0), point=4)},
        "gas_32": {
            "create_gas_32": format_float_coin(un_format_fil_to_decimal(
                history_result_32['create_gas'] if history_result_32.get('create_gas') else 0), point=4),
            "keep_gas_32": format_float_coin(un_format_fil_to_decimal(
                history_result_32['keep_gas'] if history_result_32.get('keep_gas') else 0), point=4)
        }
    }
    result_dict['history_time_gas'] = history_time_gas

    # 查询昨日质押相关
    # rr_api_result = RRMine().get_fil_overview()
    # rr_fil_overview = rr_api_result.get("datas")
    result_dict['rr_fil_overview'] = OverViewBase().rr_fil_overview()
    return format_return(0, data=result_dict)


@common_ajax_response
def get_overview_day_records(request):
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    request_dict = {
        "start_date": start_date,
        "end_date": end_date
    }

    result = inner_server.get_net_ovewview_day_records(request_dict)
    for i in range(len(result['data'])):
        result['data'][i]['create_gas_32_overview'] = format_fil(result['data'][i]['create_gas_32_overview'])
        result['data'][i]['create_gas_64_overview'] = format_fil(result['data'][i]['create_gas_64_overview'])
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_miner_list_by_raw_power(request):
    is_pool = request.POST.get('is_pool')
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    request_dict = {
        "is_pool": is_pool,
        "page_index": page_index,
        "page_size": page_size
    }
    # result_list = []
    miner_rank_result = inner_server.get_miner_list(request_dict)
    # company_mapping = inner_server.get_miner_to_company_mapping().get('data')
    # data_list = miner_rank_result.get("data").get("objs") if miner_rank_result.get("data") else []
    # for miner_info in data_list:
    #     miner_info['company'] = company_mapping.get(miner_info.get("miner_no"))
    #     result_list.append(miner_info)
    return format_return(0, data=miner_rank_result.get("data"))


@common_ajax_response
def get_miner_list_by_power_inc(request):
    stats_type = request.POST.get('stats_type', '24h')
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    request_dict = {
        "page_index": page_index,
        "page_size": page_size
    }
    if stats_type == "24h":
        miner_rank_result = inner_server.get_miner_list_by_power_inc_24(request_dict)
    else:
        end_date = datetime.date.today() - datetime.timedelta(days=1)
        start_date = end_date - datetime.timedelta(days=int(stats_type[0:stats_type.find("d")]))
        request_dict["start_date"] = start_date
        request_dict["end_date"] = end_date
        miner_rank_result = inner_server.get_miner_list_by_power_inc(request_dict)
    return format_return(0, data=miner_rank_result.get("data"))


@common_ajax_response
def get_miner_list_by_block(request):
    stats_type = request.POST.get('stats_type','24h')
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    request_dict = {
        "stats_type": stats_type,
        "page_index": page_index,
        "page_size": page_size
    }
    miner_rank_result = inner_server.get_miner_list_by_block(request_dict)
    return format_return(0, data=miner_rank_result.get("data"))


@common_ajax_response
def get_miner_list_by_avg_reward(request):
    stats_type = request.POST.get('stats_type', '24h')
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    request_dict = {
        "page_index": page_index,
        "page_size": page_size
    }
    if stats_type == "24h":
        miner_rank_result = inner_server.get_miner_list_by_avg_reward_24(request_dict)
    else:
        end_date = datetime.date.today() - datetime.timedelta(days=1)
        start_date = end_date - datetime.timedelta(days=int(stats_type[0:stats_type.find("d")]))
        request_dict["start_date"] = start_date
        request_dict["end_date"] = end_date
        miner_rank_result = inner_server.get_miner_list_by_avg_reward(request_dict)
    return format_return(0, data=miner_rank_result.get("data"))


@common_ajax_response
def get_base_fee_trends(request):
    # page_index = int(request.POST.get('page_index', '1'))
    # page_size = min(int(request.POST.get('page_size', '10')), 50)
    # request_dict = {
    #     "page_index": page_index,
    #     "page_size": page_size,
    # }

    request_dict = request.POST.dict()
    result = inner_server.get_base_fee_trends(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_gas_stat_all(request):
    request_dict = request.POST.dict()
    result = inner_server.get_gas_stat_all(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_gas_cost_stat(request):
    request_dict = request.POST.dict()
    result = inner_server.get_gas_cost_stat(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_message_list(request):
    request_dict = request.POST.dict()
    # is_next = json.loads(request.POST.get('is_next', '0'))
    # timestamp = int(request.POST.get('timestamp', 0))
    # miner_no = request.POST.get('miner_no')
    #
    # request_dict = {
    #     "is_next": is_next,
    #     "timestamp": timestamp,
    #     "miner_no": miner_no,
    # }

    result = inner_server.get_message_list(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_memory_pool_message(request):
    page_index = int(request.POST.get('page_index', '1'))
    page_size = min(int(request.POST.get('page_size', '10')), 50)
    request_dict = {
        "page_index": page_index,
        "page_size": page_size,
    }

    result = inner_server.get_memory_pool_message(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_tipsets(request):
    height = request.POST.get("height")
    page_index = int(request.POST.get('page_index', '1'))
    page_size = min(int(request.POST.get('page_size', '10')), 50)
    request_dict = {
        "page_index": page_index,
        "page_size": page_size,
        "height": height
    }

    result = inner_server.get_tipsets(request_dict)
    result = result.get("data")
    result.update({"now": datetime.datetime.now()})
    return format_return(0, data=result)


@common_ajax_response
def search(request):
    value = request.POST.get('value')
    if not value:
        return format_return(16004)
    data = OverViewBase().search_type(value)
    if not data:
        return format_return(16004)
    return format_return(0, data=data)


@common_ajax_response
def search_miner_or_wallet(request):
    value = request.POST.get('value')
    if not value:
        return format_return(16004)
    data = OverViewBase().search_miner_or_wallet(value)
    if not data:
        return format_return(16004)
    return format_return(0, data=data)


@common_ajax_response
def search_miner_type(request):
    value = request.POST.get('value')
    if not value:
        return format_return(16004)
    data = OverViewBase().search_miner_type(value)
    if not data:
        return format_return(16004)
    return format_return(0, data=data)


# @common_ajax_response
# def get_miner_tag(request):
#     params = MinerTagQuerySerializer(data=request.POST)
#     if params.is_valid():
#         data = list()
#         tags = OverViewBase().get_miner_tag()
#         if 'miner_no_list' in params.validated_data:
#             miner_no_list = list()
#             for i in params.validated_data['miner_no_list']:
#                 resp = BingheEsBase().get_is_miner(i)
#                 if resp.get('hits'):
#                     miner_no_list.append(i)
#                 else:
#                     resp = BingheChainBase().address_to_miner_no(i)
#                     if resp['data'] != 'invalid':
#                         miner_no_list.append(resp['data'])
#             for tag in tags:
#                 if tag['miner_no'] in miner_no_list:
#                     data.append(tag)
#         else:
#             data = tags
#         return format_return(0, data=data)
#     else:
#         return format_return(99904, msg='参数错误')


@common_ajax_response
def sync_miner_tag(request):
    date_time = MinerBase.objects.filter().first().day
    miner_list = list(MinerBase.objects.filter(day=date_time).values_list("miner_no", flat=True))
    traverse_dict = {
        1: miner_list,
        2: [],
        3: [],
        4: [],
        5: []
    }
    for key, value in traverse_dict.items():
        print('当前剩余矿工数:{}'.format(len(value)))
        for miner_no in value:
            miner_overview = FilfoxBase().get_miner_overview(miner_no)
            try:
                miner_tag = miner_overview.get('tag').get("name")
            except:
                # 如果获取到了id,那么说明没有异常,只是没有标签
                if not miner_overview.get('id'):
                    # 等待后重复调用还是不会有结果
                    time.sleep(61)
                    # 判断下一个需要遍历的对象是否存在
                    if isinstance(traverse_dict.get(key + 1), list):
                        traverse_dict.get(key + 1).append(miner_no)
                    else:
                        pass
            else:
                if miner_tag:
                    with transaction.atomic():
                        obj = MinerApplyTag.objects.filter(miner_no=miner_no)
                        # if not obj:
                        #     MinerApplyTag.objects.create(miner_no=miner_no, en_tag=miner_tag, cn_tag=miner_tag)
                        if obj:
                            if obj.first().signed:
                                continue
                            obj.delete()
                        MinerApplyTag.objects.create(miner_no=miner_no, en_tag=miner_tag, cn_tag=miner_tag)
                        time.sleep(0.5)
    # OverViewBase().get_miner_tag(must_update_cache=True)
    return format_return(0)


@common_ajax_response
def get_miner_apply_tag(request):
    params = MinerTagQuerySerializer(data=request.POST)
    if params.is_valid():
        data = list()
        apply_tags = MinerApplyTag.objects.filter(status=True).all()
        apply_tags = MinerApplyTagSerializer(apply_tags, many=True).data
        if 'miner_no_list' in params.validated_data:
            for tag in apply_tags:
                if tag['miner_no'] in params.validated_data['miner_no_list'] or tag['address'] in params.validated_data[
                    'miner_no_list']:
                    data.append(tag)
        else:
            data = apply_tags
        return format_return(0, data=data)
    return format_return(99904, msg='参数错误')


@common_ajax_response
def set_miner_apply_tag(request):
    params = MinerApplyTagSetSerializer(data=request.POST)
    if params.is_valid():
        bhc = BingheChainBase()
        miner_no = params.validated_data['miner_no']
        cn_tag = params.validated_data.get('cn_tag')
        en_tag = params.validated_data['en_tag']
        address = params.validated_data['address']
        contact = params.validated_data['contact']
        sign_bytes = params.validated_data['sign_bytes']
        miner_apply_tag = MinerApplyTag.objects.filter(miner_no=miner_no).first()
        resp = bhc.verify_signature(address, sign_bytes)
        if resp.get('data') == 'valid':
            if miner_apply_tag:
                miner_apply_tag.cn_tag = cn_tag
                miner_apply_tag.en_tag = en_tag
                miner_apply_tag.contact = contact
                miner_apply_tag.signed = True
            else:
                miner_apply_tag = MinerApplyTag(miner_no=miner_no, address=address, cn_tag=cn_tag, en_tag=en_tag,
                                                contact=contact, signed=True)
            miner_apply_tag.save()
            data = MinerApplyTagSerializer(miner_apply_tag).data
            return format_return(0, data=data)
    return format_return(99904, msg='参数错误')


@common_ajax_response
def miner_tag_classify(request):
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 100)), 1000)
    # objs = MinerApplyTag.objects.filter(status=True).all()
    #
    # data_result = Page(objs, page_size).page(page_index)
    # request_dict = {
    #     "miner_no_list": json.dumps([obj.miner_no for obj in data_result["objects"]]),
    #     "page_index": 1,
    #     "page_size": page_size
    # }
    # miner_result = inner_server.get_miner_list_by_miners(request_dict)
    # miner_dict = {}
    # for miner_ in miner_result.get("data", {}).get("objects", []):
    #     miner_dict[miner_["miner_no"]] = {"power": miner_["power"], "power_str": format_power(miner_["power"])}
    # data_objects = []
    # for obj in data_result["objects"]:
    #     tmp = {
    #         "miner_no": obj.miner_no,
    #         "en_tag": obj.en_tag,
    #     }
    #     tmp.update(miner_dict.get(obj.miner_no, {"power": "0", "power_str": "0"}))
    #     data_objects.append(tmp)
    # data_result["objects"] = data_objects

    request_dict = {
        "page_index": page_index,
        "page_size": page_size
    }
    miner_result = inner_server.get_miner_list_by_miners(request_dict)
    miner_no_list = [obj["miner_no"] for obj in miner_result.get("data", {}).get("objects", [])]

    objs = MinerApplyTag.objects.filter(status=True, miner_no__in=miner_no_list).all()
    miner_tag_dict = {}
    for miner_tag in objs:
        miner_tag_dict[miner_tag.miner_no] = {"en_tag": miner_tag.en_tag}

    data_objects = []
    for obj in miner_result.get("data", {}).get("objects", []):
        tmp = {
            "miner_no": obj["miner_no"],
            "power": obj["power"],
            "power_str": format_power(obj["power"]),
            "sector_size": obj["sector_size"],
            "sector_size_str": format_power(obj["sector_size"])
        }
        tmp.update(miner_tag_dict.get(obj["miner_no"], {"en_tag": ""}))
        data_objects.append(tmp)
    miner_result["data"]["objects"] = data_objects
    return format_return(0, data=miner_result.get("data"))


@common_ajax_response
def get_tag_status(request):
    tag_status = TagStatus.objects.filter().first()
    return format_return(0, data=tag_status.status if tag_status else False)