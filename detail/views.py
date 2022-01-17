import json

from django.shortcuts import render
from datetime import datetime, timedelta, date

from detail.interface import DetailBase
from xm_s_common.third.binghe_sdk import BingheEsBase
from xm_s_common.utils import format_return, format_power, format_fil, format_fil_to_decimal, _d,un_format_fil_to_decimal
from xm_s_common.decorator import common_ajax_response
from xm_s_common import inner_server
from master_overview.interface import OverViewBase
import time


@common_ajax_response
def get_tipset_by_height(request):
    height = request.POST.get('height')
    request_dict = {
        "height": height
    }
    result = inner_server.get_tipset_by_height(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_message_detail(request):
    msg_cid = request.POST.get('msg_cid')
    request_dict = {
        "msg_cid": msg_cid
    }
    result = inner_server.get_message_detail(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_miner_overview_by_no(request):
    miner_no = request.POST.get('miner_no')
    request_dict = {
        "miner_no": miner_no,
    }
    data_result = inner_server.get_miner_by_no(request_dict)
    if not data_result.get('data'):
        result = BingheEsBase().get_pool_miner_detail(miner_no)
        if result.get("hits"):
            miner_detail = result.get("hits")[0].get("_source")
            miner_wallet_search = BingheEsBase().get_pool_miner_wallet_detail(miner_no)
            if not miner_wallet_search.get("hits"):
                pass
            else:
                miner_detail.update(miner_wallet_search.get("hits")[0].get("_source"))
            result_dict = {
                "avg_reward": 0.00,  # 产出效率
                "increase_power": "0",
                "increase_power_24": "0",
                "increase_power_offset": "0",
                "increase_power_offset_24": "0",
                "initial_pledge_balance": miner_detail.get("initial_pledge"),  # 扇区质押
                "initial_pledge": miner_detail.get("initial_pledge"),  # 奖励锁仓
                "balance": miner_detail.get("total_balance_value"),  # 账户余额,
                "available_balance": miner_detail.get("available_balance_value"),  # 可用金额,
                "active_sector": 0,  # 全部扇区
                "faulty_sector": 0,  # 失败的扇区
                "block_reward": 0,  # 出块奖励
                "ranking": "--",  # 排名,
                "miner_no": miner_detail.get("miner_id"),  # 矿工号,

            }
            result_dict.update(miner_detail)

            return format_return(0, data=result_dict)
        else:
            return format_return(0, data=data_result.get("data"))

    else:
        return format_return(0, data=data_result.get("data"))


@common_ajax_response
def get_miner_line_chart_by_no(request):
    miner_no = request.POST.get('miner_no')
    stats_type = request.POST.get('stats_type')
    request_dict = {
        "miner_no": miner_no,
        "stats_type": stats_type,
    }
    result = inner_server.get_miner_line_chart_by_no(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_calculate_block_and_reward(request):
    """
    预测的出块和奖励
    :param request:
    :return:
    """
    day_ = datetime.now().strftime("%Y-%m-%d")
    result = []
    # 指定矿工算力
    miner_no = request.POST.get('miner_no')
    request_dict = {
        "miner_no_list": json.dumps([miner_no]),
        "page_index": 1,
        "page_size": 20
    }
    miner_result = inner_server.get_miner_list_by_miners(request_dict)
    power = _d(0)
    for miner_ in miner_result.get("data", {}).get("objects", []):
        power = _d(miner_["power"]) /_d(1024 ** 4)
    # 预测
    request_dict = {
        "luck_v": 0.997,
        "days": 30
    }
    calculator_result = inner_server.get_calculator_get_lookups(request_dict)
    for data in calculator_result.get("data"):
        if data.get("date") >= day_:
            block_reward = _d(data.get("avg_reward")) * power
            block_count = round(block_reward / (_d(data.get("reward_by_luck")) / 2880 / 5))
            result.append(dict(date=data.get("date"), block_reward=round(un_format_fil_to_decimal(block_reward)),
                               block_count=block_count))
    return format_return(0, data=result)


@common_ajax_response
def get_miner_gas_by_no(request):
    """矿工的gas消耗"""
    miner_no = request.POST.get('miner_no')
    stats_type = request.POST.get('stats_type', '7d')

    end_date = datetime.today() - timedelta(days=1)
    if stats_type == "7d":
        start_date = end_date - timedelta(days=7)
    if stats_type == "30d":
        start_date = end_date - timedelta(days=30)
    if stats_type == "90d":
        start_date = end_date - timedelta(days=90)
    request_dict = {
        "miner_no": miner_no,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "page_index": 1,
        "page_size": 100
    }
    is_32 = False
    miner_day_result = {}
    result = inner_server.get_miner_day_records(request_dict)
    increase_power = _d(0)
    increase_power_offset = _d(0)
    total_gas = _d(0)
    create_total_gas = _d(0)
    total_pledge_gas = _d(0)
    # 矿工每天的数据
    if result.get("code") == 0:
        for miner_day in result.get("data").get("objs", []):
            is_32 = True if miner_day["sector_size"] == "34359738368" else False  # 是否是32扇区
            increase_power += _d(miner_day.get("increase_power"))
            increase_power_offset += _d(miner_day.get("increase_power_offset"))
            day_create_total_gas = _d(miner_day["pre_gas"]) + _d(miner_day["prove_gas"]) + _d(miner_day["overtime_pledge_fee"])
            create_total_gas += day_create_total_gas
            day_total_gas = day_create_total_gas + _d(miner_day["win_post_gas"])
            total_gas += day_total_gas
            total_pledge_gas += _d(miner_day.get("pledge_gas"))
            day_create_gas = format_fil((day_create_total_gas / (_d(miner_day.get("increase_power")) / _d(1024 ** 4))) if miner_day.get("increase_power") != "0" else 0)
            miner_day_result[miner_day.get("date")] = dict(day_create_gas=day_create_gas)

    data = []  # 图表数据
    over_result = inner_server.get_net_ovewview_day_records(request_dict)  # 全网每天数据
    if over_result.get("code") == 0:
        for overview_day in over_result.get("data"):
            per_date = overview_day["date"]
            overview_day_create_gas = overview_day["create_gas_32_overview"] if is_32 else overview_day[
                "create_gas_64_overview"]
            miner_day_dict = miner_day_result.get(per_date, dict(day_create_gas=0))
            miner_day_dict["overview_day_create_gas"] = format_fil(overview_day_create_gas)
            miner_day_dict["date"] = per_date
            data.append(miner_day_dict)
    # 组合图标和总计的数据值
    result = dict(day_increase_power=format_power(increase_power),
                  day_increase_power_offset=format_power(increase_power_offset),
                  day_total_gas=format_fil(total_gas),
                  day_pledge_gas=total_pledge_gas,
                  day_create_gas=format_fil((create_total_gas/(increase_power / _d(1024 ** 4))) if increase_power else 0),
                  objs=data
                  )
    # 全网总的统计
    over_gas = inner_server.get_gas_sum_by_per(dict(start_date=start_date.strftime("%Y-%m-%d"),
                                                    end_date=end_date.strftime("%Y-%m-%d"),
                                                    sector_type=0 if is_32 else 1))
    result["day_overview_create_gas"] = over_gas.get("data", 0)
    result["day_gas_offset"] = _d(result["day_create_gas"]) - _d(result["day_overview_create_gas"])
    return format_return(0, data=result)


@common_ajax_response
def get_miner_day_gas_list_by_no(request):
    miner_no = request.POST.get('miner_no')
    start_date = request.POST.get('start_date', datetime.today().strftime("%Y-%m-%d"))
    end_date = request.POST.get('end_date')
    page_index = request.POST.get('page_index', '1')
    page_size = min(int(request.POST.get('page_size', '10')), 100)
    request_dict = {
        "miner_no": miner_no,
        "start_date": start_date,
        "page_index": page_index,
        "page_size": page_size
    }
    # 如果要查询今天 并时间小于8点。则推辞一天（原因质押是每天7点半更新）
    if datetime.today().strftime("%Y-%m-%d") == start_date and datetime.now() < datetime.now().replace(hour=7, minute=30):
        request_dict["start_date"] = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    if end_date:
        request_dict["end_date"] = end_date

    result = inner_server.get_miner_day_records(request_dict)
    # 矿工每天的数据
    if result.get("code") == 0:
        result_list = []
        for value in result.get("data").get("objs", []):
            create_total_gas = _d(value["pre_gas"]) + _d(value["prove_gas"]) + _d(value["overtime_pledge_fee"])
            win_post_gas = _d(value["win_post_gas"])
            result_list.append(dict(
                date=value["date"],
                increase_power=format_power(value["increase_power"]),
                increase_power_offset=format_power(value["increase_power_offset"]),
                create_total_gas=create_total_gas,
                pledge_gas=value["pledge_gas"],
                win_post_gas=win_post_gas,
                total_gas=format_fil_to_decimal(create_total_gas + win_post_gas, 4),
                create_gas=format_fil_to_decimal((create_total_gas / (_d(value["increase_power"]) / _d(1024**4))) if value["increase_power"]!="0" else 0, 4),
                win_gas=(win_post_gas / (_d(value["power"]) / _d(1024 ** 4))) if value["power"] !="0" else 0,
            ))
        result["data"]["objs"] = result_list
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_transfer_list_by_no(request):
    miner_no = request.POST.get('miner_no')
    msg_method = request.POST.get('msg_method')
    page_index = request.POST.get('page_index', '1')
    page_size = min(int(request.POST.get('page_size', '10')), 100)
    start_time = request.POST.get('start_date')
    end_time = request.POST.get('end_date')
    request_dict = {
        "miner_id": miner_no,
        "msg_method": msg_method,
        "start_time": start_time,
        "end_time": end_time,
        "page_index": page_index,
        "page_size": page_size
    }
    result = inner_server.get_transfer_list(request_dict)
    tag_set = set()
    tag_dict = {}
    for tmp in result.get("data", {}).get("objects", []):
        tag_set.add(tmp["msg_from"])
        tag_set.add(tmp["msg_to"])
    if tag_set:
        tags = OverViewBase().get_miner_tag_by_miner(miner_no_list=list(tag_set))
        tag_dict = {tag.miner_no: [tag.cn_tag, tag.en_tag, tag.signed] for tag in tags}
    for tmp in result.get("data", {}).get("objects", []):
        tmp["msg_from_tag"] = tag_dict.get(tmp["msg_from"], [])
        tmp["msg_to_tag"] = tag_dict.get(tmp["msg_to"], [])
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_miner_blocks(request):
    miner_no = request.POST.get('miner_no')
    page_index = request.POST.get('page_index')
    page_size = request.POST.get('page_size')
    start_time = request.POST.get('start_date')
    end_time = request.POST.get('end_date')
    request_dict = {
        "miner_no": miner_no,
        "start_time": start_time,
        "end_time": end_time,
        "page_index": page_index,
        "page_size": page_size
    }
    result = inner_server.get_miner_blocks(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_block_message(request):
    block_id = request.POST.get('block_id')
    msg_method = request.POST.get('msg_method')
    page_index = request.POST.get('page_index')
    page_size = request.POST.get('page_size')
    request_dict = {
        "block_id": block_id,
        "msg_method": msg_method,
        "page_index": page_index,
        "page_size": page_size
    }
    result = inner_server.get_block_message(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_message_list(request):
    is_next = json.loads(request.POST.get('is_next', '0'))
    timestamp = int(request.POST.get('timestamp', 0))
    current_start_index = int(request.POST.get('current_start_index', 0))
    scroll_id = request.POST.get('scroll_id')
    miner_no = request.POST.get('miner_no')
    page_size = int(request.POST.get('page_size', 20))
    page_index = int(request.POST.get('page_index', 1))
    msg_method = 'msg_method' in request.POST and int(request.POST.get('msg_method')) or None

    request_dict = {
        "is_next": is_next,
        "timestamp": timestamp,
        "miner_no": miner_no,
        "page_size": page_size,
        "page_index": page_index,
        "msg_method": msg_method,
        'current_start_index': current_start_index,
        'scroll_id': scroll_id,
        "all": request.POST.get("all", False)
    }

    result = inner_server.get_message_list(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_tipset_by_block_cid(request):
    block_id = request.POST.get('block_id')
    request_dict = {
        "block_id": block_id
    }

    result = inner_server.get_block_detail(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_miner_wallet_line_chart_by_no(request):
    data_type = request.POST.get("data_type")
    miner_no = request.POST.get("miner_no")
    start_time = request.POST.get("start_time")
    end_time = request.POST.get("end_time")
    if not start_time or not end_time:
        end_time = date.today() + timedelta(days=1)
        start_time = end_time - timedelta(30)
    else:
        end_time = (datetime.strptime(end_time, "%Y-%m-%d") + timedelta(days=1)).date()
        start_time = datetime.strptime(start_time, "%Y-%m-%d").date()
    end_time_temp_time = time.mktime(end_time.timetuple())
    start_time_temp_time = time.mktime(start_time.timetuple())
    result = DetailBase().get_line(data_type, miner_no, start_time_temp_time, end_time_temp_time)
    return format_return(0, data=result)


@common_ajax_response
def get_miner_mining_stats_by_no(request):
    miner_no = request.POST.get("miner_no")
    stats_type = request.POST.get("stats_type")
    request_dict = {
        "miner_no": miner_no,
        "stats_type": stats_type
    }

    result = inner_server.get_miner_mining_stats_by_no(request_dict)
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_deal_list(request):
    key_words = request.POST.get('key_words')
    page_size = request.POST.get('page_size')
    page_index = request.POST.get('page_index')
    request_dict = {
        "page_size": page_size and int(page_size) or 30,
        "page_index": page_index and int(page_index) or 1
    }
    if key_words:
        request_dict["key_words"] = key_words
    result = inner_server.get_deal_list(request_dict)
    # 添加Tag标签
    tag_set = set()
    tag_dict = {}
    for tmp in result.get("data", {}).get("objs", []):
        tag_set.add(tmp["client"])
        tag_set.add(tmp["provider"])
    if tag_set:
        tags = OverViewBase().get_miner_tag_by_miner(miner_no_list=list(tag_set))
        tag_dict = {tag.miner_no: [tag.cn_tag, tag.en_tag, tag.signed] for tag in tags}
    for tmp in result.get("data", {}).get("objs", []):
        tmp["client_tag"] = tag_dict.get(tmp["client"], [])
        tmp["provider_tag"] = tag_dict.get(tmp["provider"], [])
    return format_return(0, data=result.get("data"))


@common_ajax_response
def get_deal_info(request):
    result = inner_server.get_deal_info(dict(deal_id=request.POST.get("deal_id")))
    return format_return(0, data=result.get("data"))
