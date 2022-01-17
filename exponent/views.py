from django.shortcuts import render
from datetime import datetime, timedelta

from exponent.models import MinerIndex
from exponent.serializer import MinerIndexSerializer, CompanyMinerIndexSerializer, MinerIndexLineSerializer, \
    MinerIndexRankSerializer, CompanyIndexLineSerializer
from xm_s_common.utils import format_return
from xm_s_common.decorator import common_ajax_response, add_request_log
from exponent.interface import IndexBase, IndexQueryBase
from xm_s_common import inner_server


# Create your views here.

@common_ajax_response
@add_request_log()
def sync_data_miner(request):
    """
    数据中台同步数据到本地,写入矿工基础数据,并计算矿工的7项指数具体数值
    :return:
    """
    date = request.POST.get('date')
    if not date:
        date = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')
    # 写入基础数据,计算指数
    IndexBase().sync_data(date)
    return format_return(0)


@common_ajax_response
def sync_data_miner_company(request):
    """
    计算矿工的数据的集合,合并为矿商数据
    """
    date = request.POST.get('date')
    if not date:
        date = datetime.strftime(datetime.now(), '%Y-%m-%d')
    # 写入基础数据,计算指数
    IndexBase().sync_data_miner_company(date)
    return format_return(0)


@common_ajax_response
def get_miner_index(request):
    miner_type = get_miner_type(request.POST.get("miner_type", "big"))
    miner_no = request.POST.get('miner_no')
    if not miner_no:
        miner_no = IndexQueryBase.newest_miner(miner_type)
    miner_obj = MinerIndex.objects.filter(miner_no=miner_no)
    if miner_obj:
        miner_type = miner_obj[0].miner_type
    else:
        return format_return(15000, msg='矿工不存在')
    method = request.POST.get("method")  # miner_矿工 statistics 综合
    miner_obj = IndexQueryBase().get_miner_index(miner_no, method, miner_type)
    serializer = MinerIndexSerializer(miner_obj, many=True)
    return format_return(0, data=serializer.data)


@common_ajax_response
def get_miner_index_line(request):
    miner_type = get_miner_type(request.POST.get("miner_type", "big"))

    miner_no = request.POST.get('miner_no')
    if not miner_no:
        miner_no = IndexQueryBase.newest_miner(miner_type)

    miner_obj = MinerIndex.objects.filter(miner_no=miner_no)
    if miner_obj:
        miner_type = miner_obj[0].miner_type
    else:
        return format_return(15000, msg='矿工不存在')

    method = request.POST.get("method")  # miner_矿工 statistics 综合
    start_time = request.POST.get("start_time")
    end_time = request.POST.get("end_time")
    if not start_time or not end_time:
        end_time = datetime.strftime(datetime.now(), "%Y-%m-%d")
        start_time = datetime.strftime(datetime.now() - timedelta(days=6), "%Y-%m-%d")
    miner_obj = IndexQueryBase().get_miner_index_line(miner_no, method, start_time, end_time, miner_type)
    serializer = MinerIndexSerializer(miner_obj, many=True)
    return format_return(0, data=serializer.data)


@common_ajax_response
def get_company_index(request):
    miner_type = get_miner_type(request.POST.get("miner_type", "big"))
    company_code = request.POST.get('company_code')
    if not company_code:
        company_code = IndexQueryBase.newest_company()
    method = request.POST.get("method")  # company_矿商 statistics 综合
    miner_obj = IndexQueryBase().get_company_index(company_code, method, miner_type)
    serializer = CompanyMinerIndexSerializer(miner_obj, many=True)
    return format_return(0, data=serializer.data)


@common_ajax_response
def get_company_index_line(request):
    company_code = request.POST.get('company_code')
    if not company_code:
        company_code = IndexQueryBase.newest_company()

    method = request.POST.get("method")  # company_矿工 statistics 综合
    start_time = request.POST.get("start_time")
    end_time = request.POST.get("end_time")
    if not start_time or not end_time:
        end_time = datetime.strftime(datetime.now(), "%Y-%m-%d")
        start_time = datetime.strftime(datetime.now() - timedelta(days=6), "%Y-%m-%d")
    miner_obj = IndexQueryBase().get_company_index_line(company_code, method, start_time, end_time)
    serializer = CompanyIndexLineSerializer(miner_obj, many=True)
    return format_return(0, data=serializer.data)


@common_ajax_response
def get_miner_ranking(request):
    miner_type = get_miner_type(request.POST.get("miner_type", "big"))

    company_miner_dict = inner_server.get_miner_to_company_mapping()
    # 7项指标
    index_list = ["avg_reward", "total_power", "day_inc_rate", "avg_inc_rate", "create_gas_week",
                  "keep_gas_week", "section_fault_rate", "power_increment_7day"]
    result_dict = {}
    for index in index_list:
        query_set = IndexQueryBase().get_miner_rank(index, miner_type)
        serializer = MinerIndexRankSerializer(instance=query_set, fields={"miner_no", index + "_v", index + "_i"},
                                              context={"company": company_miner_dict.get("data")}, many=True)
        result_dict[index] = serializer.data
    # 综合评分
    synthesize_query_set = IndexQueryBase().get_miner_rank("synthesize", miner_type)
    serializer = MinerIndexRankSerializer(instance=synthesize_query_set,
                                          fields={"miner_no", "synthesize_i", "synthesize_rank"},
                                          context={"company": company_miner_dict.get("data")}, many=True)
    result_dict["synthesize"] = serializer.data

    return format_return(0, data=result_dict)


@common_ajax_response
def get_company_ranking(request):
    miner_type = get_miner_type(request.POST.get("miner_type", "big"))
    # 7项指标
    index_list = ["avg_reward", "total_power", "day_inc_rate", "avg_inc_rate", "create_gas_week",
                  "keep_gas_week", "section_fault_rate", "power_increment_7day"]
    result_dict = {}
    for index in index_list:
        query_set = IndexQueryBase().get_company_rank(index, miner_type)
        serializer = CompanyMinerIndexSerializer(instance=query_set,
                                                 fields={"company_name", index + "_v", index + "_i"}, many=True)
        result_dict[index] = serializer.data
    # 综合评分
    synthesize_query_set = IndexQueryBase().get_company_rank("synthesize", miner_type)
    serializer = CompanyMinerIndexSerializer(instance=synthesize_query_set,
                                             fields={"company_name", "synthesize_i", "synthesize_rank"}, many=True)
    result_dict["synthesize"] = serializer.data

    return format_return(0, data=result_dict)


@common_ajax_response
def get_company_list(request):
    result = inner_server.get_company_miner_mapping()

    return format_return(0, data=list(result.get('data').values()))


@common_ajax_response
def get_miner_to_company_mapping(request):
    return format_return(0, data=inner_server.get_miner_to_company_mapping().get('data'))


def get_miner_type(miner_type):
    if miner_type == "big":
        return 1
    else:
        return 2
