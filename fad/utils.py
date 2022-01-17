import decimal
from datetime import datetime, date, timedelta
from typing import List, Tuple

from xm_s_common import consts
from xm_s_common.mq.mq_kafka import Producer, MQ_TOPIC_SYS_ERROR
import requests
from pytrends.request import TrendReq

from xm_s_common.raw_sql import exec_sql
from xm_s_common.third.binghe_sdk import BingheEsBase

import pymysql

# from xm_s_common.inner_server import get_gas_stat_all

from .models import Scores, Latitudess

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
    "F099Balance": "当日消耗Gas",
    # 需要获取今日凌晨的新增地址数和24h前的
    "WalletCount": "新增地址数",
    # 需要获取今日凌晨的质押数和24h前的
    "ThisEpochPledgeCollateral": "当日新增质押",
    # 需要获取今日凌晨的链上转账数和24h前的
    "trans_count": "链上转账数",
    # 2021-05-12 新增
    "forks": "forks数量",  # 21
    "stars": "stars数量",
    "mine_cost": "挖矿成本",
    "turnover_ratio": "换手率",
}

DATABASES = {
    'default': {
        # 配置使用mysql
        'ENGINE': 'django.db.backends.mysql',  # 数据库产品
        'HOST': "139.199.60.153",  # 数据库ip
        'PORT': 3306,  # 数据库端口
        'USER': "root",  # 用户名
        'PASSWORD': "dc123456.",  # 密码
        'NAME': "index_db",  # 数据库名
    }
}


def format_input_date(origin_query):
    '''格式化输入日期，返回格式为date()'''
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
    except Exception as e:
        query_date = None
    finally:
        return query_date


def alter_line(*args, **kwargs):
    '''修改基线脚本'''
    '''
    today:当天（date结构）
    t1：当天（str结构）
    target_day：作为基准的日期（str结构）
    time_：运行时间
    real_time_data1：查到到作为新基准的数据
    sub_id：作为新基准的子维度的id
    
    '''
    today_ = date.today()
    t1 = today_.strftime('%Y-%m-%d')
    target_day = (today_ - timedelta(days=1)).strftime('%Y-%m-%d')
    time_ = datetime.now()

    # 找出前一日的数据
    sql_query = "SELECT real_time_data ,sub_dimension_id FROM  fad_scores  WHERE tag=%s AND `day` =%s;"
    res = exec_sql(sql_query, params=(0, target_day))

    # 查询今天是否已经修改了基线
    sql_query = "SELECT real_time_data ,sub_dimension_id FROM  fad_scores  WHERE tag=%s AND `day` =%s;"
    res_today = exec_sql(sql_query, params=(1, t1))

    # 查询今日的基线记录是否存在，若不存在则直接创建，若存在，则不做任何处理
    if not res_today:
        for real_time_data1, sub_id in res:
            sql_query1 = 'INSERT INTO fad_scores (ref_data,real_time_data,day,create_time,sub_dimension_id,tag) ' \
                         'VALUES (%s,%s,%s,%s,%s,' \
                         '%s); '
            exec_sql(
                sql_query1, params=(real_time_data1, 0, t1, time_, sub_id, 1))


def record_main_dimension(*args, **kwargs):
    '''每日记录主维度的数据'''
    # 查询出前一日的数据
    # 将前一日到数据记录下来
    '''
    today:当天（date结构）
    t1：当天（str结构）
    target_day：作为基准的日期（str结构）
    time_：运行时间
    
    '''
    # 时间处理
    today_ = date.today()
    # t1 = today_.strftime('%Y-%m-%d')
    target_day = (today_ - timedelta(days=1)).strftime('%Y-%m-%d')
    time_ = datetime.now()
    # 数据库连接

    # 查询数据
    sql_query = "SELECT weighting_factor,weighing_scores,(SELECT aParent_id FROM fad_latitudess WHERE id = " \
                "sub_dimension_id) as pid,(SELECT ratio FROM fad_latitudess WHERE id=(SELECT aParent_id FROM " \
                "fad_latitudess WHERE id = sub_dimension_id)) as ratio,sub_dimension_id FROM fad_scores WHERE tag=%s " \
                "and day=%s and sub_dimension_id IN (SELECT id FROM fad_latitudess WHERE is_active=1) ORDER BY pid;"
    res1 = exec_sql(sql_query, params=(0, target_day))
    if not res1:
        print('errpr: data not found!')
        return None
    result = number_apart(res1)
    query_exists = "SELECT * FROM  xm_s_explorer.fad_latitudehistory WHERE day=%s;"
    res2 = exec_sql(query_exists, params=(target_day,))
    if not res2:
        for k, v in result.items():
            lati_id = k
            grade = v[0]
            ratio = v[1]
            query_lan = "INSERT INTO xm_s_explorer.fad_latitudehistory (grade, ratio,day,create_time,lati_id) VALUES(%s,%s,%s,%s,%s)"
            exec_sql(query_lan, params=(grade, ratio, target_day, time_, lati_id))


def number_apart(src: Tuple):
    '''用于辅助计算主维度得分'''
    # dict1用于记录初步值
    # dict2用于记录最终值
    dict1 = {}
    dict2 = {}
    for i in src:
        if i[2] not in dict1:
            dict1.setdefault(i[2], [])
            dict1[i[2]].append(i[1])
            dict1[i[2]].append(i[0])
            dict1[i[2]].append(i[3])

        else:
            dict1[i[2]][0] += i[1]
            dict1[i[2]][1] += i[0]

    for k, v in dict1.items():
        dict2[k] = [v[0] / v[1], v[2]]

    return dict2


# 以下是定时任务

# 获取子维度真实数据

def get_sev(res_today):
    """格式化ES里面的数据 24"""
    dict_1 = {}
    # 将值添加入字典
    try:
        dict_1['MinerAboveMinPowerCount'] = res_today['hits'][0]['_source']['MinerAboveMinPowerCount']
        dict_1['MinerCount'] = res_today['hits'][0]['_source']['MinerCount']
        dict_1['ThisEpochQualityAdjPower'] = res_today['hits'][0]['_source']['ThisEpochQualityAdjPower']
        # TODO 将流通量改为换手率
        # dict_1['CirculSupply'] = res_today['hits'][0]['_source']['CirculSupply']
        # 以下3个为差值
        dict_1['WalletCount'] = res_today['hits'][0]['_source']['WalletCount']
        # dict_1['ThisEpochPledgeCollateral'] = res_today['hits'][0]['_source']['ThisEpochPledgeCollateral']
        # dict_1['F099Balance'] = res_today['hits'][0]['_source']['F099Balance']
    except Exception as e:
        from xm_s_common import debug
        detail = debug.get_debug_detail(e)
        Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'fad', 'url': 'get_sev', 'detail': detail})
        return dict_1
    return dict_1


def read_data():
    """ 获取其他七个值  通过inner_server.get_deal_stat(height)获取"""
    """ 需要凌晨6点调用 """
    dict_1 = {}
    # 获取此时高度
    des = date.today()
    des_yes = des - timedelta(days=1)
    height_today = int((datetime(des.year, des.month, des.day, 0, 0, 0).timestamp() -
                        datetime(2020, 8, 25, 6, 0, 0).timestamp()) / 30)
    height_yesterday = int((datetime(des_yes.year, des_yes.month, des_yes.day, 0, 0, 0).timestamp() -
                            datetime(2020, 8, 25, 6, 0, 0).timestamp()) / 30)

    binhe = BingheEsBase()
    # 需要获取今天和昨天的值
    res_today = binhe.get_index_overview(height_today)
    res_yesterday = binhe.get_index_overview(height_yesterday)
    if not res_today or not res_yesterday:
        return {'a': 'not found'}

    dict_1['MinerAboveMinPowerCount'] = res_today['hits'][0]['_source']['MinerAboveMinPowerCount']
    dict_1['MinerCount'] = res_today['hits'][0]['_source']['MinerCount']
    dict_1['ThisEpochQualityAdjPower'] = res_today['hits'][0]['_source']['ThisEpochQualityAdjPower']
    # dict_1['CirculSupply'] = res_today['hits'][0]['_source']['CirculSupply'].split()[0]
    # 以下3个为差值
    dict_1['WalletCount'] = res_today['hits'][0]['_source']['WalletCount'] - \
                            res_yesterday['hits'][0]['_source']['WalletCount']
    # dict_1['ThisEpochPledgeCollateral'] = decimal.Decimal(
    #     res_today['hits'][0]['_source']['ThisEpochPledgeCollateral']) - \
    #                                       decimal.Decimal(
    #                                           res_yesterday['hits'][0]['_source']['ThisEpochPledgeCollateral'])
    # dict_1['F099Balance'] = decimal.Decimal(res_today['hits'][0]['_source']['F099Balance'].split()[0]) - \
    #                         decimal.Decimal(res_yesterday['hits'][0]['_source']['F099Balance'].split()[0])
    # 获取子维度数据

    for k, v in dict_1.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = decimal.Decimal(v)
        basic_scores = real_time_data / ref_data
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                    basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
    return dict_1


# def get_coin_info():
#     """ 获取FIL币价（$），交易市值，交易额 共三个数据 5 6 7 24"""
#     dict_1 = {}
#     for i in range(10):
#         try:
#             url = "https://fxhapi.feixiaohao.com/public/v1/ticker?limit=300"
#             res = requests.get(url=url)
#             for i in res.json():
#                 if i['name'] == 'Filecoin':
#                     dict_1['price_usd'] = i['price_usd']
#                     dict_1['volume_24h_usd'] = i['volume_24h_usd']
#                     dict_1['market_cap_usd'] = i['market_cap_usd']
#                     dict_1['turnover_ratio'] = i['volume_24h_usd'] / i['market_cap_usd']
#             break
#         except Exception as e:
#             from xm_s_common import debug
#             detail = debug.get_debug_detail(e)
#             Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'fad', 'url': 'get_coin_info()', 'detail': detail})
#             continue
#     for k, v in dict_1.items():
#         # 获取子维度的name
#         sub_dimension_name = frame_mapping[k]
#         # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
#         res_sub_dict = get_submention_info(sub_dimension_name)
#         sub_dimension_id = res_sub_dict['sub_dimension_id']
#         # weighting_factor
#         weighting_factor = res_sub_dict['weighting_factor']
#         res_ref_dict = get_ref_data(sub_dimension_id)
#         # 获取基准数据
#         ref_data = res_ref_dict['ref_data']
#         # 获取实时数据
#         real_time_data = decimal.Decimal(v)
#         basic_scores = real_time_data / ref_data
#         weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
#         # 插入数据
#         insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
#                     basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
#     return dict_1


def get_coin_info():
    """ 获取FIL币价（$），交易市值，交易额 共三个数据 5 6 7 24"""
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'd59aa2e1-7b51-4b03-b8b0-08785bd30ae5',
    }
    dict_1 = {}
    for i in range(10):
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=FIL"
            res = requests.get(url=url, headers=headers, timeout=20)
            usd_data = res.json().get('data').get('FIL').get('quote').get('USD')
            dict_1['price_usd'] = usd_data.get('price')
            dict_1['volume_24h_usd'] = usd_data.get('volume_24h')
            dict_1['market_cap_usd'] = usd_data.get('market_cap')
            dict_1['turnover_ratio'] = usd_data.get('volume_24h') / usd_data.get('market_cap')
            break
        except Exception as e:
            from xm_s_common import debug
            detail = debug.get_debug_detail(e)
            Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'fad', 'url': 'get_coin_info()', 'detail': detail})
            continue
    for k, v in dict_1.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = decimal.Decimal(v)
        basic_scores = real_time_data / ref_data
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                    basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
    return dict_1


def get_mine_cost():
    """挖矿成本=昨日质押+昨日消耗64G扇区gas+昨日消耗32G扇区"""
    data_dict = {}
    current_date = date.today() - timedelta(days=1)
    url = f"https://browserapi.bingheyc.com/v1/data/asset/all/{current_date.strftime('%Y-%m-%d')}"
    headers = {"Authorization": "Basic YmluZ2hlaGVubGl1Ymk6NjA4NzRmNzFmMGRiNDZlNTg2Y2Y3NWQ5ODQyMzU0MjM="}
    res = requests.get(url=url, headers=headers).json()['data']
    mine_cost = ((res["dayPackingGasFee32"] + res["dayPackingGasFee64"]) / res["dayPackingNum"]) + res[
        "unitTPackingPledgeFee"]
    data_dict['mine_cost'] = mine_cost

    for k, v in data_dict.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = v
        basic_scores = decimal.Decimal(real_time_data) / decimal.Decimal(ref_data)
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                    basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
    return data_dict


def get_git_commits():
    """ 获取git commits数量 一个子维度"""
    data_dict = {}
    start_time = (
        (date.today() - timedelta(days=1) - timedelta(hours=8))
            .strftime("%Y-%m-%dT%H:%M:%S%z")
            .replace('+0000', 'Z')
    )
    end_time = (
        (date.today() - timedelta(hours=8))
            .strftime("%Y-%m-%dT%H:%M:%S%z")
            .replace('+0000', 'Z')
    )
    res = None
    for i in range(10):
        try:
            res = requests.get(
                f'https://api.github.com/repos/filecoin-project/lotus/commits?since="{start_time}"&until="{end_time}"&per_page=100')
            break
        except Exception as e:
            from xm_s_common import debug
            detail = debug.get_debug_detail(e)
            Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'fad', 'url': 'get_git_commits()', 'detail': detail})
            continue
    if not res:
        return 'error'
    data_dict['git_commits_num'] = len(res.json())
    # data_dict[start_time.split('T')[0]] = len(res.json())
    # 获取子维度数据
    for k, v in data_dict.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = v
        basic_scores = real_time_data / ref_data
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                    basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
    return data_dict


def get_git_fork_star_count():
    """获取git项目的fork和star数量"""
    data_dict = {}
    res = None
    for i in range(10):
        try:
            res = requests.get(
                f'https://api.github.com/repos/filecoin-project/lotus')
            break
        except Exception as e:
            from xm_s_common import debug
            detail = debug.get_debug_detail(e)
            Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'fad', 'url': 'get_git_fork_star_count', 'detail': detail})
            continue
    if not res:
        return 'error'
    data_dict['forks'] = res.json()['forks']
    data_dict['stars'] = res.json()['watchers']
    for k, v in data_dict.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = v
        basic_scores = real_time_data / ref_data
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                    basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
    return data_dict


def get_transaction_num():
    """ 获取链上转账数 一个子维度"""
    dict_ = {}
    # 调用接口获取链上转账数
    start_date = datetime(date.today().year, date.today().month, date.today().day, 0, 0, 0)
    height = int((start_date.timestamp() - datetime(2020, 8, 25, 6, 0, 0).timestamp()) / 30)
    try:
        data = BingheEsBase().get_msg_value(height).get('sector_group').get('buckets')[0].get('gas_sum').get('value')
    except Exception as e:
        from xm_s_common import debug
        detail = debug.get_debug_detail(e)
        Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'fad', 'url': 'get_transaction_num', 'detail': detail})
        data = 0
    if not data:
        return 'error---data=None'
    res = decimal.Decimal(data) / (10 ** 18)
    if not res:
        return 'error---res=None'

    # 将链上转账数放到字典中
    dict_["trans_count"] = res
    for k, v in dict_.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = decimal.Decimal(v)
        basic_scores = real_time_data / ref_data
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                    basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
    return dict_


def get_google_index():
    """ 获取谷歌指数 1个子维度 """
    dict_ = {}
    # 获取谷歌子维度数据
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    data = {'empty': True}
    for i in range(10):
        try:
            pytrend = TrendReq(hl='zh-hans', tz=480)
            keywords = ['Filecoin']
            pytrend.build_payload(kw_list=keywords, cat=0, timeframe='now 7-d', gprop='')
            data = pytrend.interest_over_time()
            break
        except Exception as e:
            from xm_s_common import debug
            detail = debug.get_debug_detail(e)
            Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'fad', 'url': 'get_google_index()', 'detail': detail})
            continue
    if data.get('empty'):
        val = Scores.objects.filter(sub_dimension__id=15).order_by('-create_time').first().real_time_data
        dict_['google_index'] = int(val)
    else:
        val_list = data.get(yesterday).values.tolist()
        total = 0
        for i in val_list:
            total += i[0]
        val = int(total / len(val_list))
        # 将子维度数据保存下来，放到字典中
        dict_['google_index'] = val
    for k, v in dict_.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = decimal.Decimal(v)
        basic_scores = real_time_data / ref_data
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                    basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
    return dict_


def get_storage_info():
    """ 获取存储订单量和存储数据大小 2个子维度 """
    dict_ = {}
    # 获取数据
    res = requests.get(url=f'{consts.SERVER_DATA}/data/api/deal/get_deal_stat')
    # 将数据放入字典中
    dict_['deal_size'] = res.json()['data']['deal_size']
    dict_['deal_count'] = res.json()['data']['deal_count']
    # 获取子维度数据
    for k, v in dict_.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = decimal.Decimal(v)
        basic_scores = real_time_data / ref_data
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_data(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                    basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id)
    return dict_


# 插入数据到数据库


def insert_data(weighting_factor, ref_data, real_time_data, basic_score, weighing_scores, sub_dimension_id):
    # 准备需要传入的数据
    day = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    create_time = datetime.now()
    # 先判断数据是否存在，若不存在则插入数据，若存在则什么都不做
    sql_query_lan = "SELECT * FROM fad_scores WHERE tag=%s and day=%s and sub_dimension_id=%s "
    res = exec_sql(sql_query_lan, params=(0, day, sub_dimension_id))
    if res:
        return None

    # 插入数据
    sql_insert_lan = "INSERT INTO fad_scores (weighting_factor,ref_data,real_time_data,basic_scores," \
                     "weighing_scores,day,create_time,tag,sub_dimension_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);"
    status = exec_sql(sql_insert_lan, (weighting_factor, ref_data, real_time_data, basic_score, weighing_scores,
                                       day, create_time, 0, sub_dimension_id))


# 获取基准数据


def get_ref_data(sid):
    """通过sub_dimension_id获取对应到基准数据  """
    """ sbi:传入之前获取的子维度的submention_id """
    dict_ = {}
    sql_get_ref_data = "SELECT  ref_data  FROM  fad_scores fsc WHERE tag =1 and day=(SELECT DISTINCT day FROM  " \
                       "fad_scores fsc WHERE tag=1 ORDER BY day DESC LIMIT 1) and sub_dimension_id =%s;"
    res = exec_sql(sql_get_ref_data, params=(sid,))
    dict_['ref_data'] = res[0][0]
    return dict_


# 获取子维度id和权重

# 计算值basic_score和weighting_score
def cal_score():
    '''计算基础得分和权重得分'''
    sql_query = 'SELECT id,weighting_factor ,ref_data ,real_time_data FROM fad_scores fs WHERE tag=0 and ref_data<>0 ' \
                'and real_time_data <>0 and basic_scores =0 ; '

    res = exec_sql(sql_query)
    if not res:
        return None
    for tem in res:
        sid, factor, ref, real = tem
        basic_score = real / ref
        weighting_score = decimal.Decimal(factor) * basic_score
        sql_insert = 'UPDATE fad_scores SET basic_scores =%s, weighing_scores =%s WHERE id=%s;'
        exec_sql(sql_insert, params=(basic_score, weighting_score, sid))


def get_submention_info(sdn):
    """ 获取子维度id和权重 """
    '''sdn: sub_dimension_name'''
    dict_ = {}

    # 获取子维度的id和权重
    sql_sub_dimention_info = 'SELECT id ,weighting_factor FROM fad_latitudess fl  WHERE name = %s ;'
    r = exec_sql(sql_sub_dimention_info, params=(sdn,))
    dict_['sub_dimension_id'] = r[0][0]
    dict_['weighting_factor'] = r[0][1]
    return dict_


# 以下函数仅供补数据需要
def cal_scorei():
    '''计算基础得分和权重得分'''
    sql_query = 'SELECT id,weighting_factor ,ref_data ,real_time_data FROM fad_scores fs WHERE tag=0 and ref_data<>0 ' \
                'and real_time_data <>0 ; '

    res = exec_sql(sql_query)
    # if not res:
    #     return None
    for tem in res:
        sid, factor, ref, real = tem
        basic_score = real / ref
        weighting_score = decimal.Decimal(factor) * basic_score
        sql_insert = 'UPDATE fad_scores SET basic_scores =%s, weighing_scores =%s WHERE id=%s;'
        exec_sql(sql_insert, params=(basic_score, weighting_score, sid))


def read_data_i(input_date):
    """ 获取其他七个值  通过inner_server.get_deal_stat(height)获取"""
    """ 需要凌晨6点调用 """
    a = input_date.split('-')
    des = datetime(int(a[0]), int(a[1]), int(a[2]), 0, 0, 0)
    dict_1 = {}
    # 获取此时高度
    # des = input_date
    yesterday = des - timedelta(days=1)
    height_today = int((datetime(des.year, des.month, des.day, 0, 0, 0).timestamp() -
                        datetime(2020, 8, 25, 6, 0, 0).timestamp()) / 30)
    height_yesterday = int((datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0).timestamp() -
                            datetime(2020, 8, 25, 6, 0, 0).timestamp()) / 30)

    binhe = BingheEsBase()
    # 需要获取今天和昨天的值
    res_today = binhe.get_index_overview(height_today)
    res_yesterday = binhe.get_index_overview(height_yesterday)

    if not res_today and not res_yesterday:
        return {'a': 'not found'}

    dict_1['MinerAboveMinPowerCount'] = res_today['hits'][0]['_source']['MinerAboveMinPowerCount']
    dict_1['MinerCount'] = res_today['hits'][0]['_source']['MinerCount']
    dict_1['ThisEpochQualityAdjPower'] = res_today['hits'][0]['_source']['ThisEpochQualityAdjPower']
    # dict_1['CirculSupply'] = res_today['hits'][0]['_source']['CirculSupply'].split()[0]
    # 以下3个为差值
    dict_1['WalletCount'] = res_today['hits'][0]['_source']['WalletCount'] - \
                            res_yesterday['hits'][0]['_source']['WalletCount']
    # dict_1['ThisEpochPledgeCollateral'] = decimal.Decimal(
    #     res_today['hits'][0]['_source']['ThisEpochPledgeCollateral']) - \
    #                                       decimal.Decimal(
    #                                           res_yesterday['hits'][0]['_source']['ThisEpochPledgeCollateral'])
    # dict_1['F099Balance'] = decimal.Decimal(res_today['hits'][0]['_source']['F099Balance'].split()[0]) - \
    #                         decimal.Decimal(res_yesterday['hits'][0]['_source']['F099Balance'].split()[0])
    # 获取子维度数据

    for k, v in dict_1.items():
        # 获取子维度的name
        sub_dimension_name = frame_mapping[k]
        # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
        res_sub_dict = get_submention_info(sub_dimension_name)
        sub_dimension_id = res_sub_dict['sub_dimension_id']
        # weighting_factor
        weighting_factor = res_sub_dict['weighting_factor']
        res_ref_dict = get_ref_data(sub_dimension_id)
        # 获取基准数据
        ref_data = res_ref_dict['ref_data']
        # 获取实时数据
        real_time_data = decimal.Decimal(v)
        basic_scores = real_time_data / ref_data
        weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
        # 插入数据
        insert_datai(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                     basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id,
                     day=yesterday.strftime('%Y-%m-%d'))
    return dict_1


def insert_datai(weighting_factor, ref_data, real_time_data, basic_score, weighing_scores, sub_dimension_id, day):
    # 准备需要传入的数据
    day = day
    create_time = datetime.now()
    # 先判断数据是否存在，若不存在则插入数据，若存在则什么都不做
    sql_query_lan = "SELECT * FROM fad_scores WHERE tag=%s and day=%s and sub_dimension_id=%s "
    res = exec_sql(sql_query_lan, params=(0, day, sub_dimension_id))
    if res:
        return None

    # 插入数据
    sql_insert_lan = "INSERT INTO fad_scores (weighting_factor,ref_data,real_time_data,basic_scores," \
                     "weighing_scores,day,create_time,tag,sub_dimension_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);"
    status = exec_sql(sql_insert_lan, (weighting_factor, ref_data, real_time_data, basic_score, weighing_scores,
                                       day, create_time, 0, sub_dimension_id))


def record_main_dimensioni(date_):
    '''每日记录主维度的数据'''
    # 查询出前一日的数据
    # 将前一日到数据记录下来
    '''
    today:当天（date结构）
    t1：当天（str结构）
    target_day：作为基准的日期（str结构）
    time_：运行时间
    
    '''

    # 时间处理
    target_day = date_
    time_ = datetime.now()
    # 数据库连接

    # 查询数据
    # sql_query = "SELECT weighting_factor,weighing_scores,(SELECT aParent_id FROM fad_latitudess WHERE id = sub_dimension_id) " \
    #             "as pid,(SELECT ratio FROM fad_latitudess WHERE id=(SELECT aParent_id FROM fad_latitudess WHERE id = sub_dimension_id))" \
    #             " as ratio FROM fad_scores WHERE tag=%s " \
    #             "and day=%s;"

    sql_query = "SELECT weighting_factor,weighing_scores,(SELECT aParent_id FROM fad_latitudess WHERE id = " \
                "sub_dimension_id) as pid,(SELECT ratio FROM fad_latitudess WHERE id=(SELECT aParent_id FROM " \
                "fad_latitudess WHERE id = sub_dimension_id)) as ratio,sub_dimension_id FROM fad_scores WHERE tag=%s " \
                "and day=%s and sub_dimension_id IN (SELECT id FROM fad_latitudess WHERE is_active=1) ORDER BY pid;"
    res1 = exec_sql(sql_query, params=(0, target_day))
    if not res1:
        print('error: data not found!')
        return None
    result = number_apart(res1)
    query_exists = "SELECT * FROM  xm_s_explorer.fad_latitudehistory WHERE day=%s;"
    res2 = exec_sql(query_exists, params=(target_day,))
    if not res2:
        for k, v in result.items():
            print(k, v)
            lati_id = k
            grade = v[0]
            ratio = v[1]
            query_lan = "INSERT INTO xm_s_explorer.fad_latitudehistory (grade, ratio,day,create_time,lati_id) VALUES(%s,%s,%s,%s,%s)"
            exec_sql(query_lan, params=(grade, ratio, target_day, time_, lati_id))
    else:
        for k, v in result.items():
            print(k, v)
            lati_id = k
            grade = v[0]
            ratio = v[1]
            query_lan = f"UPDATE xm_s_explorer.fad_latitudehistory SET grade=%s, ratio=%s WHERE lati_id=%s and day=%s"
            ret = exec_sql(query_lan, params=(grade, ratio, lati_id, target_day))


tmp_dict = {
    5: "price_usd",
    7: "volume_24h_usd",
    6: "market_cap_usd",
    4: "CirculSupply",
    10: "ThisEpochQualityAdjPower",
    11: "MinerCount",
    12: "MinerAboveMinPowerCount",
    16: "git_commits_num",
    19: "deal_count",
    20: "deal_size",
    15: "google_index",
    14: "F099Balance",
    8: "WalletCount",
    13: "ThisEpochPledgeCollateral",
    9: "trans_count",
    21: "forks",
    22: "stars",
    23: "mine_cost",
    24: "turnover_ratio",
}


def import_new_data(dt):
    conn = pymysql.connect(host='192.168.88.58', port=3306, user='root', passwd='gc123456.', database='xm_s_explorer')
    cur = conn.cursor()
    conn.commit()
    if not dt:
        dt = date(2020, 10, 15)
    while dt < date.today():
        data_dict = {}
        query_lang = "SELECT * FROM fad WHERE date = %s"
        cur.execute(query_lang, (dt,))
        res = cur.fetchall()
        # res = exec_sql(query_lang, (dt.strftime('%Y-%m-%d')))
        for i in res:
            data_dict[tmp_dict.get(i[3])] = decimal.Decimal(i[1])
        for k, v in data_dict.items():
            # 获取子维度的name
            sub_dimension_name = frame_mapping[k]
            # {'sub_dimension_id': 16, 'weighting_factor': 1.0}
            res_sub_dict = get_submention_info(sub_dimension_name)
            sub_dimension_id = res_sub_dict['sub_dimension_id']
            # weighting_factor
            weighting_factor = res_sub_dict['weighting_factor']
            res_ref_dict = get_ref_data(sub_dimension_id)
            # 获取基准数据
            ref_data = res_ref_dict['ref_data']
            # 获取实时数据
            real_time_data = v
            basic_scores = real_time_data / ref_data
            weighing_scores = basic_scores * decimal.Decimal(weighting_factor)
            # 插入数据
            print(ref_data, real_time_data, basic_scores, weighing_scores)

            insert_datai(weighting_factor=weighting_factor, ref_data=ref_data, real_time_data=real_time_data,
                         basic_score=basic_scores, weighing_scores=weighing_scores, sub_dimension_id=sub_dimension_id,
                         day=dt)
        dt += timedelta(days=1)
    cur.close()
    conn.close()


def calculate_new_weighting_factor():
    """计算更新子维度权重后的得分"""
    scs = Scores.objects.filter(tag=0)
    for i in scs:
        print(i.day)
        i.basic_scores = i.real_time_data / i.ref_data
        i.weighing_scores = i.basic_scores * decimal.Decimal(i.weighting_factor)
        i.save()


def refresh_weighting_factor():
    """刷新子维度权重"""
    tem_dict = {}
    lts = Latitudess.objects.all()
    for i in lts:
        tem_dict[i.id] = i.weighting_factor
    scs = Scores.objects.all()
    for i in scs:
        i.weighting_factor = tem_dict.get(i.sub_dimension.id)
        i.save()
    calculate_new_weighting_factor()
    print('done')


def refresh_record_main_dimension():
    """刷新主维度数据"""
    dt = date(2020, 10, 15)
    while dt < date.today():
        print(dt)
        record_main_dimensioni(dt)
        dt += timedelta(days=1)
