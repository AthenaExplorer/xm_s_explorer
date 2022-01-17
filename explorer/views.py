import re
import time

from django.utils import timezone

from xm_s_common.decorator import common_ajax_response
from xm_s_common.utils import format_return
from xm_s_common.third.binghe_chain_sdk import BingheChainBase
from explorer.interface import ExplorerBase, ExplorerQueryBase
from pro.serializers import *


@common_ajax_response
def get_block_chart(request):
    data = ExplorerBase().get_block_chart_by_Filscan()
    return format_return(0, data=data)


@common_ajax_response
def get_overview(request):
    data = ExplorerBase().get_overview()
    return format_return(0, data=data)


@common_ajax_response
def get_hashrate_ranking(request):
    data = ExplorerBase().get_hashrate_ranking_from_can()
    return format_return(0, data=data)


@common_ajax_response
def get_power_valid(request):
    page_size = request.POST.get('page_size', 50)
    page_index = request.POST.get('page_index', 0)
    count = request.POST.get('count', 0)
    data = ExplorerBase().get_power_valid(page_index, page_size, count)
    return format_return(0, data=data)


@common_ajax_response
def get_blocks(request):
    page_size = request.POST.get('page_size', 50)
    page_index = request.POST.get('page_index', 0)
    duration = request.POST.get('duration', "24h")  # 7d,30d,1y
    count = request.POST.get('count', 0)
    data = ExplorerBase().get_blocks(duration + str(page_index), page_index, page_size, count, duration)
    return format_return(0, data=data)


@common_ajax_response
def get_power_growth(request):
    page_size = request.POST.get('page_size', 50)
    page_index = request.POST.get('page_index', 0)
    duration = request.POST.get('duration', "24h")  # 7d,30d,1y
    count = request.POST.get('count', 0)
    data = ExplorerBase().get_power_growth(duration + str(page_index), page_index, page_size, count, duration)
    return format_return(0, data=data)


@common_ajax_response
def get_tipset(request):
    page_size = request.POST.get('page_size', 50)
    page_index = request.POST.get('page_index', 0)
    count = request.POST.get('count', 0)
    data = ExplorerBase().get_tipset(page_index, page_size, count)
    return format_return(0, data=data)


@common_ajax_response
def get_message_list(request):
    page_size = request.POST.get('page_size', 50)
    page_index = request.POST.get('page_index', 0)
    count = request.POST.get('count', 0)
    data = ExplorerBase().get_message_list(page_index, page_size, count)
    return format_return(0, data=data)


@common_ajax_response
def get_block_statistics(request):
    data = ExplorerBase().get_block_statistics()
    return format_return(0, data=data)


@common_ajax_response
def address_overview(request, address_id):
    data = ExplorerQueryBase().get_miner_overview(address_id)
    return format_return(0, data=data)


@common_ajax_response
def address_balance(request, address_id):
    detail = request.POST.get("detail")
    data = ExplorerQueryBase().get_miner_address_balance(address_id, detail)
    return format_return(0, data=data)


@common_ajax_response
def address_power_stats(request, address_id):
    data = ExplorerQueryBase().get_address_power_stats(address_id)
    return format_return(0, data=data)


@common_ajax_response
def address_mining_stats(request, address_id):
    duration = request.POST.get("duration", "24h")
    data = ExplorerQueryBase().address_mining_stats(address_id, duration)
    return format_return(0, data=data)


@common_ajax_response
def address_message(request, address_id):
    page_size = request.POST.get("page_size")
    page = request.POST.get("page_index")
    data = ExplorerQueryBase().address_message(address_id, page_size, page)
    return format_return(0, data=data)


@common_ajax_response
def peer_info(request, peer_id):
    data = ExplorerQueryBase().peer_info(peer_id)
    return format_return(0, data=data)


@common_ajax_response
def address_power_overview(request, address_id):
    data = ExplorerQueryBase().address_power_overview(address_id)
    return format_return(0, data=data)


@common_ajax_response
def search(request):
    value = request.POST.get('value')
    if not value:
        return format_return(16002)
    data = ExplorerBase().search(value)
    return data


@common_ajax_response
def block_high_info(request, high_value):
    for i in range(5):
        try:
            data = ExplorerQueryBase().block_high_info(high_value)
            return format_return(0, data=data)
        except:
            time.sleep(1)

    return format_return(16002)


@common_ajax_response
def block_id_info(request, block_id):
    for i in range(5):
        try:
            data = ExplorerQueryBase().block_id_info(block_id)
            return format_return(0, data=data)
        except:
            time.sleep(1)

    return format_return(16002)


@common_ajax_response
def message_info_by_message_id(request, message_id):
    for i in range(5):
        try:
            data = ExplorerQueryBase().get_message_info_by_message_id(message_id)
            return format_return(0, data=data)
        except:
            time.sleep(1)

    return format_return(16002)


@common_ajax_response
def by_block_id_message_list(request, block_id):
    page_size = request.POST.get('page_size', 50)
    page_index = request.POST.get('page_index', 0)
    data = ExplorerQueryBase().by_block_id_message_list(block_id, page_index, page_size)
    return format_return(0, data=data)


@common_ajax_response
def get_block_distribution(request):
    data = ExplorerBase().get_block_distribution()
    return format_return(0, data=data)


@common_ajax_response
def get_miner_power_increment_tendency(request):
    count = request.POST.get('count', 5)
    duration = request.POST.get('duration', "7d")
    samples = request.POST.get('samples', 7)
    redis_key = str(count) + duration + str(samples)
    data = ExplorerBase().get_miner_power_increment_tendency(redis_key, count, duration, samples)
    return format_return(0, data=data)


@common_ajax_response
def get_mining_earnings(request):
    duration = request.POST.get("duration", "7d")
    data = ExplorerBase().get_mining_earnings(duration)
    return format_return(0, data=data)


@common_ajax_response
def get_sector_pledge(request):
    duration = request.POST.get("duration", "7d")
    data = ExplorerBase().get_sector_pledge(duration)
    return format_return(0, data=data)


@common_ajax_response
def get_gas_tendency(request):
    duration = request.POST.get("duration", "24h")
    samples = request.POST.get("samples", "48")
    redis_key = duration + samples
    data = ExplorerBase().get_gas_tendency(redis_key, duration, samples)
    return format_return(0, data=data)


@common_ajax_response
def get_gas_data_24h(request):
    data = ExplorerBase().get_gas_data_24h()
    return format_return(0, data=data)


@common_ajax_response
def address_to_miner_no(request):
    address = request.POST.get('address')
    resp = BingheChainBase().address_to_miner_no(address)
    data = resp.get('data')
    if data == 'invalid':
        return format_return(99904)
    return format_return(0, data)
