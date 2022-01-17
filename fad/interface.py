from decimal import Decimal
from datetime import datetime, date, timedelta

from django.db.models import Q

from xm_s_common.raw_sql import exec_sql
from .models import Scores, LatitudeHistory, Latitudess
from .serializers import LatitudeHistorySer
import pandas as pd
from xm_s_common.third.binghe_sdk import BingheEsBase

frame_mapping = {
    "price_usd": "币价",
    "volume_24h_usd": "交易额",
    "market_cap_usd": "FIL流通市值",
    "CirculSupply": "流通量",
    "ThisEpochQualityAdjPower": "有效算力",
    "MinerCount": "参与矿工数",
    "MinerAboveMinPowerCount": "活跃矿工数",
    "git_commits_num": "github提交数",
    "deal_count": "存储订单量",
    "deal_size": "存储数据大小",
    "google_index": "google指数",

    # 需要获取今日凌晨的消耗量和24h前的
    "F099Balance": "当日消耗Gas(FIL)",
    # 需要获取今日凌晨的新增地址数和24h前的
    "WalletCount": "新增地址数",
    # 需要获取今日凌晨的质押数和24h前的
    "ThisEpochPledgeCollateral": "当日新增质押(FIL)",
    # 需要获取今日凌晨的链上转账数和24h前的
    "trans_count": "链上转账数",
}


def read_data():
    """ 获取其他七个值  通过inner_server.get_deal_stat(height)获取"""
    """ 需要凌晨6点调用 """
    dict_1 = {}
    # 获取此时高度
    des = datetime.today()
    yes = des - timedelta(days=1)
    height_today = int((datetime(des.year, des.month, des.day, 0, 0, 0).timestamp() -
                        datetime(2020, 8, 25, 6, 0, 0).timestamp()) / 30)
    height_yesterday = int((datetime(yes.year, yes.month, yes.day).timestamp() -
                            datetime(2020, 8, 25, 6, 0, 0).timestamp()) / 30)
    binhe = BingheEsBase()
    # 需要获取今天和昨天的值
    res_today = binhe.get_index_overview(height_today)
    res_yesterday = binhe.get_index_overview(height_yesterday)
    # 将值添加入字典
    dict_1['MinerAboveMinPowerCount'] = res_today['hits'][0]['_source']['MinerAboveMinPowerCount']
    dict_1['MinerCount'] = res_today['hits'][0]['_source']['MinerCount']
    dict_1['ThisEpochQualityAdjPower'] = int(res_today['hits'][0]['_source']['ThisEpochQualityAdjPower'])
    dict_1['CirculSupply'] = Decimal(res_today['hits'][0]['_source']['CirculSupply'].split(' ')[0])
    # 以下3个为差值
    dict_1['WalletCount'] = res_today['hits'][0]['_source']['WalletCount'] - \
                            res_yesterday['hits'][0]['_source']['WalletCount']
    dict_1['ThisEpochPledgeCollateral'] = Decimal(res_today['hits'][0]['_source']['ThisEpochPledgeCollateral']) - \
                                          Decimal(res_yesterday['hits'][0]['_source']['ThisEpochPledgeCollateral'])
    dict_1['F099Balance'] = Decimal(res_today['hits'][0]['_source']['F099Balance'].split(' ')[0]) - Decimal(
        res_yesterday['hits'][0]['_source']['F099Balance'].split(' ')[0])
    return dict_1


def data_details(query_date):
    '''做主维度、子维度以及FIL指数处理 给get_details用'''
    scores_details = Scores.objects.filter(day=query_date, sub_dimension__is_active=True, tag=0)
    his = LatitudeHistory.objects.filter(day=query_date)
    return (scores_details, his)


def fil_index_changed(query_date):
    '''用于计算FIL指数'''
    # 新一天的
    his = LatitudeHistory.objects.filter(day=query_date)
    ser = LatitudeHistorySer(his, many=True)
    total_new = 0
    for i in ser.data:
        total_new += i['grade'] * i['ratio']
    # total_new *= 1000
    # 前一天的
    date_yesterday = query_date - timedelta(days=1)
    his = LatitudeHistory.objects.filter(day=date_yesterday)
    if not his:
        changed = 'null'
        return total_new, changed
    ser = LatitudeHistorySer(his, many=True)
    total_old = 0
    for i in ser.data:
        total_old += i['grade'] * i['ratio']
    # total_old *= 1000
    changed = f'{round((total_new - total_old) / total_old * 100, 2)}'
    return total_new, changed


def fil_index_7_changed(query_date):
    '''用于计算FIL指数'''
    # 新一天的
    his = LatitudeHistory.objects.filter(day=query_date)
    ser = LatitudeHistorySer(his, many=True)
    total_new = 0
    for i in ser.data:
        total_new += i['grade'] * i['ratio']
    # total_new *= 1000
    # 前一天的
    date_yesterday = query_date - timedelta(days=7)
    his = LatitudeHistory.objects.filter(day=date_yesterday)
    if not his:
        changed = 'null'
        return total_new, changed
    ser = LatitudeHistorySer(his, many=True)
    total_old = 0
    for i in ser.data:
        total_old += i['grade'] * i['ratio']
    # total_old *= 1000
    changed = f'{round((total_new - total_old) / total_old * 100, 2)}'
    return total_new, changed


def fil_index_30_changed(query_date):
    '''用于计算FIL指数'''
    # 新一天的
    his = LatitudeHistory.objects.filter(day=query_date)
    ser = LatitudeHistorySer(his, many=True)
    total_new = 0
    for i in ser.data:
        total_new += i['grade'] * i['ratio']
    # total_new *= 1000
    # 前一天的
    date_yesterday = query_date - timedelta(days=30)
    his = LatitudeHistory.objects.filter(day=date_yesterday)
    if not his:
        changed = 'null'
        return total_new, changed
    ser = LatitudeHistorySer(his, many=True)
    total_old = 0
    for i in ser.data:
        total_old += i['grade'] * i['ratio']
    # total_old *= 1000
    changed = f'{round((total_new - total_old) / total_old * 100, 2)}'
    return total_new, changed


def switch_inter(id, switch):
    dict_ = {}
    if id and switch:
        dict_ = {'id': id, 'switch': switch}
        instance = Latitudess.objects.filter(id=id).first()
        instance.is_active = switch
        instance.save()
    return dict_


def change_factor(id, factor):
    dict_1 = {}
    if id and factor:
        dict_1 = {'id': id, 'factor': factor}
        ins = Latitudess.objects.filter(Q(id=id) & ~Q(aParent=None))
        if not ins:
            res_dict = {'error': '请不要尝试修改主维度或不存在的子维度'}
            return res_dict
        ins[0].weighting_factor = float(factor)
        ins[0].save()
    else:
        dict_1 = {'error': 'missing elements'}
    return dict_1


def change_kospi(ratio):
    dict_1 = {}
    if ratio:
        dict_1 = {'ratio': ratio}
        ratio = ratio.strip('').split(':')
        r1 = int(ratio[0])
        r2 = int(ratio[1])
        r3 = int(ratio[2])
        if r1 + r2 + r3 != 10:
            res_dict = {'error': '输入比例有误，请重新输入'}
            return res_dict
        for index, ins in enumerate(Latitudess.objects.filter(aParent=None)):
            ins.ratio = int(ratio[index]) / 10
            ins.save()
    return dict_1


def get_newest_fil_index():
    i = 0
    while True:
        date = (datetime.now() - timedelta(days=i)).date()
        fil_index_objs = LatitudeHistory.objects.filter(day=date)
        if fil_index_objs.count() == 3:
            df = pd.DataFrame(list(fil_index_objs.values('grade', 'ratio')))
            fil_index_value = (df['grade'] * df['ratio']).sum()
            return fil_index_value * 1000
        else:
            i += 1
        if i > 10:
            return 0
