import decimal
import time
from datetime import date, timedelta, datetime

from xm_s_common.inner_server import get_gas_stat_all
from xm_s_common.utils import format_return
from xm_s_common.third.binghe_sdk import BingheEsBase
from xm_s_common.decorator import common_ajax_response
from xm_s_common.utils import format_power, format_fil

from .models import Latitudess, Scores, LatitudeHistory
from .serializers import LatitudessSer, LatitudeHistorySer, ScoresSer, ParentLatitudessSer, FactorSer
from .interface import data_details, fil_index_changed, switch_inter, change_factor, change_kospi, fil_index_7_changed, \
    fil_index_30_changed
from .utils import alter_line, format_input_date, get_sev, cal_score, \
    get_coin_info, get_git_commits, get_storage_info, read_data, get_transaction_num, record_main_dimension, \
    get_google_index, record_main_dimensioni, cal_scorei, get_mine_cost, get_git_fork_star_count


# Create your views here.


@common_ajax_response
def get_details(request):
    # return format_return(0)
    if request.method == 'POST':
        current_time = datetime.today()
        if current_time < datetime(date.today().year, date.today().month, date.today().day, 8, 5, 0):
            today = date.today() - timedelta(days=2)
        else:
            today = date.today() - timedelta(days=1)
        origin_query = request.POST.get('date', None)
        if origin_query:
            oqs = origin_query.strip("'").split('-')
        else:
            oqs = None
        try:
            query_date = date(
                year=int(oqs[0]),
                month=int(oqs[1]),
                day=int(oqs[2]),
            )
            if query_date >= date.today() - timedelta(days=1):
                if datetime.today() < datetime(date.today().year, date.today().month, date.today().day, 8, 5, 0):
                    query_date = date.today() - timedelta(days=2)
                else:
                    query_date = date.today() - timedelta(days=1)
            else:
                query_date = query_date


        except Exception as e:
            query_date = None
        if not query_date:
            query_date = today
        scores_details, his = data_details(query_date)
        ser1 = ScoresSer(scores_details, many=True)
        ser2 = LatitudeHistorySer(his, many=True)
        total, _ = fil_index_changed(query_date)
        return format_return(0, data={
            'sub_dimension_data': ser1.data,
            'main_dimension_data': ser2.data,
            'score': total,
        })


# FIL??????????????????

@common_ajax_response
def get_score(request):
    """??????????????????????????????"""
    current_time = datetime.today()
    if current_time < datetime(date.today().year, date.today().month, date.today().day, 8, 5, 0):
        today = date.today() - timedelta(days=2)
    else:
        today = date.today() - timedelta(days=1)
    origin_query = request.POST.get('date', None)

    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)

    query_date = format_input_date(origin_query)
    # if not query_date:
    #     query_date = today
    # self.queryset = Scores.objects.filter(
    #     tag=0, day=query_date, sub_dimension__is_active=1)

    if start_date and end_date:
        st = format_input_date(start_date)
        et = format_input_date(end_date)
        if current_time < datetime(date.today().year, date.today().month, date.today().day, 8, 5, 0):
            if et >= date.today() - timedelta(days=1):
                et = date.today() - timedelta(days=2)
        else:
            et = et

    else:
        st = today - timedelta(days=6)
        et = today
    scores_res = Scores.objects.filter(
        tag=0, sub_dimension__is_active=1, day__range=[st, et])
    ser = ScoresSer(scores_res, many=True)
    return_list = []
    b = {}
    for i in ser.data:
        b[i['day']] = {}

    for k, v in b.items():
        b[k]['day'] = k
        b[k]['score'], b[k]['changed'] = fil_index_changed(format_input_date(k))
        trash, b[k]['changed_7'] = fil_index_7_changed(format_input_date(k))
        trash, b[k]['changed_30'] = fil_index_30_changed(format_input_date(k))
        # b[k]['score'] = fil_index_changed(format_input_date(k))[0]
        # b[k]['changed'] = fil_index_changed(format_input_date(k))[1]
    for k, v in b.items():
        for i in ser.data:
            if i['day'] == k:
                b[k][i['identifier']] = i['real_time_data']

    for k, v in b.items():
        v.update({'effective_power_str': format_power(v.get('effective_power')) if v.get('effective_power') else None})
        v.update({'turnover_value_str': round(decimal.Decimal(v.get('turnover_value', 0)) / 100000000, 2)})
        v.update({'trade_vol_str': round(decimal.Decimal(v.get('trade_vol', 0)) / 100000000, 2)})
        v.update({'storage_size_str': format_power(v.get('storage_size')) if v.get('storage_size') else None})
        v.update({'impawn_daliy_str': format_fil(v.get('impawn_daliy')) if v.get('impawn_daliy') else None})
        return_list.append(v)

    return format_return(0, data=return_list)


# FIL????????????????????????
@common_ajax_response
def latitude_score(request):
    """??????FIL??????????????????"""
    if request.method == 'POST':
        current_time = datetime.today()
        if current_time < datetime(date.today().year, date.today().month, date.today().day, 8, 5, 0):
            today = date.today() - timedelta(days=2)
        else:
            today = date.today() - timedelta(days=1)

        origin_query = request.POST.get('date', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)
        # if not query_date:
        #     query_date = today
        # self.queryset = LatitudeHistory.objects.filter(day=query_date)
        if start_date and end_date:
            st = format_input_date(start_date)
            et = format_input_date(end_date)
            if et >= date.today() - timedelta(days=1):
                if datetime.today() < datetime(date.today().year, date.today().month, date.today().day, 8, 5, 0):
                    et = date.today() - timedelta(days=2)
                else:
                    et = date.today() - timedelta(days=1)
            else:
                et = et
        else:
            st = today - timedelta(days=6)
            et = today
        lh = LatitudeHistory.objects.filter(day__range=[st, et])
        ser = LatitudeHistorySer(lh, many=True)
        return_list = []
        b = {}
        for i in ser.data:
            b[i['day']] = {}

        for k, v in b.items():
            b[k]['day'] = k

        for k, v in b.items():
            for i in ser.data:
                if i['day'] == k:
                    b[k][i['identifier'] + '_' + 'ratio'] = i['ratio']
                    b[k][i['identifier'] + '_' + 'grade'] = i['grade']
        for k, v in b.items():
            return_list.append(v)

        return format_return(0, data=return_list)


@common_ajax_response
def alter_baseline(request):
    '''???????????????????????? ??????????????????????????????'''
    if request.method == 'POST':
        alter_line()
        return format_return(0, msg='????????????', data={})


# ?????????????????????????????????????????????????????????????????????????????????

@common_ajax_response
def alter_factor(request):
    '''???????????????????????????????????????'''

    factor = request.POST.get('factor', None)
    id = request.POST.get('id', None)
    res = change_factor(id=id, factor=factor)
    return format_return(0, data=res, msg='success')


# ?????????????????????????????? 4:4:2(???????????????????????????)
@common_ajax_response
def alter_scale(request):
    """??????FIL??????????????????"""
    ratio = request.POST.get('ratio', None)
    res = change_kospi(ratio)
    return format_return(0, data=res, msg='success')


# ??????????????????????????????is_active=0???

@common_ajax_response
def sub_dimension_switch(request):
    '''?????????????????????????????????'''
    # switch 0/1
    id = request.POST.get('id', None)
    switch = request.POST.get('switch', None)
    res = switch_inter(id=id, switch=switch)

    return format_return(0, data=res, msg='success')


@common_ajax_response
def cal_scores(request):
    '''?????????????????????????????????'''
    cal_score()
    return format_return(0, data={}, msg='success')


# ?????????????????????
@common_ajax_response
def time_at_0(request):
    '''0???????????????????????????????????????'''
    get_storage_info()
    get_transaction_num()
    get_coin_info()
    get_git_commits()
    get_git_fork_star_count()
    return format_return(0, data={}, msg='success')


@common_ajax_response
def time_at_8(request):
    '''8????????????ES??????7???????????????????????????????????????'''
    read_data()
    get_mine_cost()
    get_google_index()
    # ??????1???
    # time.sleep(1)
    record_main_dimension()
    return format_return(0, data={}, msg='success')


@common_ajax_response
def get_height(request):
    if request.method == 'POST':
        height = request.POST.get('height', None)
        res = BingheEsBase().get_index_overview(height)
        r = get_sev(res)
        return format_return(0, data=r)


# ??????????????????????????????
@common_ajax_response
def add_basic_score_and_weighting_score(request):
    '''??????????????????'''
    cal_scorei()
    return format_return(0, data='cali')


@common_ajax_response
def record_main_dime(request):
    """?????????????????????"""
    date_ = request.POST.get('date_')
    if not date_:
        return format_return(0)
    record_main_dimensioni(date_=date_)
    return format_return(0, data='rmd')


@common_ajax_response
def price(request):
    height = request.POST.get('height')
    res = BingheEsBase().get_height_message(height)
    # return format_return(0, data={'a': 0}, msg='success')
    return format_return(0, data=res, msg='success')


@common_ajax_response
def get_height_msg(request):
    height = request.POST.get('height')
    res = BingheEsBase().get_height_message(height).get('hits')[0].get("_source").get('base_fee2')
    return format_return(0, data=res)

