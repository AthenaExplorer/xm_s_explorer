import datetime
import decimal
import json
import re
import time
import uuid
import hashlib
from lxml import etree
import requests

from django.conf import settings
from django.db import transaction

from xm_s_common import debug, consts, inner_server, cache
from xm_s_common.decorator import validate_params, one_by_one_locked, cache_required
from xm_s_common.utils import format_return, Validator, format_power, format_fil, format_fil_to_decimal, \
    format_float_coin, format_power_to_TiB, format_coin_to_str
from xm_s_common.third.filscan_sdk import FilscanBase
from xm_s_common.third.filscout_sdk import FilscoutBase
from xm_s_common.third.filfox_sdk import FilfoxBase
import copy


class ExplorerBase(object):
    '''
    浏览器接口
    '''

    @cache_required(cache_key='explorer_block_chart', expire=30 * 1)
    def get_block_chart_by_Filscout(self, must_update_cache=False):
        '''
        查询爆块图表
        '''

        result = FilscoutBase().get_block_list()
        # result = FilscanBase().get_block_list()
        if not result or not result['data']:
            return {'miner_list': [], 'block_list_x': [], 'block_list_y': []}

        miner_list = []
        block_list_x = []
        block_dict_y = {}

        # 矿工列表
        for per in result['data']['list']:
            miner_list.append({
                'miner_address': per['miner'],
                'total_ticket': per['total_ticket'],
                'ticket_percent': per['ticket_percent'],
                'power': per['int_power'],
                'power_str': format_power(per['int_power']),
                'nick': per['nick_name']
            })

        # x轴
        block_list_x = result['data']['block_list']

        # y轴
        for per in result['data']['list_series']:
            block_dict_y["per['miner']"] = {'miner_address': per['miner'], 'data': per['data']}
        return {'miner_list': miner_list, 'block_list_x': block_list_x, 'block_list_y': block_dict_y}

    @cache_required(cache_key='explorer_block_chart', expire=30 * 1)
    def get_block_chart_by_Filscan(self, must_update_cache=False):
        '''
        查询爆块图表
        '''

        # result = FilscoutBase().get_block_list()
        print(time.time())
        result = FilscanBase().get_block_list()
        print(time.time())
        if not result or not result['result']:
            return {'miner_list': [], 'block_list_x': [], 'block_list_y': []}

        miner_list = []
        block_list_x = []
        block_list_y = []

        # 矿工列表
        for per in result['result']['topn_miners']:
            miner_list.append({
                'miner_address': per['miner'],  # 矿工id
                'total_ticket': per['block_count'],  # 出块数
                'ticket_percent': round(float(per['block_rate']) / 100, 2),  # 出块率
                'block_rate': round(float(per['block_ratio']) / 100, 2),  # 占比
                'win_count': per['win_count'],  # 赢票
                'win_count_ratio': round(float(per['win_count_ratio']) / 100, 2),  # 赢票占比
            })
        block_set = set()
        block_dict = {}
        len_tip = len(result["result"]['tipsets'])
        init_cid = ["" for i in range(len_tip)]
        init_data = [0 for i in range(len_tip)]
        # x轴
        x_list = []
        for index, tipset in enumerate(result["result"]['tipsets']):
            x_list.append(tipset['height'])  # x轴数据
            for block in tipset['blocks']:
                if block['miner'] in block_set:
                    block_dict[block['miner']][0][index] = 1
                    block_dict[block['miner']][1][index] = block['cid']
                else:
                    block_dict[block['miner']] = [copy.deepcopy(init_data), copy.deepcopy(init_cid)]
                    block_dict[block['miner']][0][index] = 1  # 写入标志
                    block_dict[block['miner']][1][index] = block['cid']  # 写入cid
                    block_set.add(block['miner'])

        return {'miner_list': miner_list, 'block_list_x': x_list, 'block_list_y': block_dict}

    @cache_required(cache_key='explorer_overview', expire=30 * 1)
    def get_overview(self, must_update_cache=False):
        # 请求飞狐数据源
        result = FilfoxBase().get_overview()
        result_2 = FilfoxBase().get_overview_2()
        if not result or not result_2:
            return {}
        html = etree.HTML(result.content.decode())
        base_xpath = r'//*[@id="__layout"]/div/div[1]/div/div[1]/div[2]/div[1]'
        # #取出数据体
        result_dict = {
            "tipset_height": html.xpath(base_xpath + "/div[1]/div/div[2]")[0].text,  # 区块集合高度
            "Latest_block_time": result_2.get('timestamp'),  # 最新区块时间
            "Net_effective_computing_power": html.xpath(base_xpath + "/div[3]/div/div[2]")[0].text,  # 全网有效算力
            "active_minaer": html.xpath(base_xpath + "/div[4]/div/div[2]")[0].text,  # 活跃矿工数
            "Rewards_per_block": html.xpath(base_xpath + "/div[5]/div/div[2]")[0].text,  # 区块奖励

            "24h_average_mining_income": html.xpath(base_xpath + "/div[6]/div/div[2]")[0].text,  # 24h平均挖矿收益
            "Nearly_24_hours_output": html.xpath(base_xpath + "/div[7]/div/div[2]")[0].text,  # 近24h产出量
            "Current_sector_pledge_volume": html.xpath(base_xpath + "/div[8]/div/div[2]")[0].text,  # 当前扇区质押量
            "FIL_pledge_amount": html.xpath(base_xpath + "/div[9]/div/div[2]")[0].text,  # FIL质押量
            "24_h_message_number": html.xpath(base_xpath + "/div[10]/div/div[2]")[0].text,  # 24h消息数

            "FIL_in_circulation": html.xpath(base_xpath + "/div[11]/div/div[2]")[0].text,  # FIL流通量
            "General_ledger_number": html.xpath(base_xpath + "/div[12]/div/div[2]")[0].text,  # 总账户数
            "Mean_block_interval": html.xpath(base_xpath + "/div[13]/div/div[2]")[0].text,  # 平均区块间隔
            "Average_number_of_blocks_per_height": html.xpath(base_xpath + "/div[14]/div/div[2]")[0].text,  # 平均每高度区块数量
            "Net_original_computing_power": html.xpath(base_xpath + "/div[15]/div/div[2]")[0].text,  # 全网原值算力

            "Current_base_rate": html.xpath(base_xpath + "/div[16]/div/div[2]")[0].text,  # 当前基础费率
            "FIL_destroyed_quantity": html.xpath(base_xpath + "/div[17]/div/div[2]")[0].text,  # FIL销毁量
            "FIL_total_supply": html.xpath(base_xpath + "/div[18]/div/div[2]")[0].text,  # FIL总供给量
            "Circulating_rate_of_FIL": html.xpath(base_xpath + "/div[19]/div/div[2]")[0].text,  # FIL流通率
            "The_latest_price": html.xpath(base_xpath + "/div[20]/div/div[2]")[0].text,  # 最新价格

        }
        return result_dict

    @cache_required(cache_key='explorer_hashrate_ranking', expire=60 * 60)
    def get_hashrate_ranking(self, must_update_cache=False):
        '''
        算力走势(有效算力)
        '''

        result = FilscoutBase().get_ranking_by_time()
        if not result or not result['data']:
            return {"miner_time_list": [], "time_list": []}
        miner_time_list = []
        # 矿工列表
        for per in result['data']['miner_time_list']:
            temp_dict = dict()
            temp_dict['miner'] = per['miner']  # 矿池矿工
            temp_dict['miner_power'] = per['miner_power']  # 有效算力_bytes
            temp_dict['power_str'] = per['power_str']  # 有效算力
            data = []
            for time_value in per['data']:
                data.append({
                    "name": time_value['name'],  # 时间:小时:分钟
                    "rate": time_value['rate'],  # 0,未知
                    "value": time_value['value'],  # 实时算力
                })
            temp_dict['data'] = data
            miner_time_list.append(temp_dict)
        # 时间列表
        time_list = result['data']['time_list']
        return {"miner_time_list": miner_time_list, "time_list": time_list}

    @cache_required(cache_key='explorer_hashrate_ranking', expire=60 * 60)
    def get_hashrate_ranking_from_can(self, must_update_cache=False):
        result = FilscanBase().get_hashrate_ranking()
        if not result:
            return {"miner_time_list": [], "time_list": []}
        miner_time_list = []
        time_list = []
        i = 0
        for miner, miner_data_list in result['result']['power_points'].items():
            temp_dict = {}
            temp_dict['miner'] = miner
            data = []
            for miner_data in miner_data_list:
                temp = {}
                temp['value'] = miner_data['power']
                temp['power_ratio'] = miner_data['power_ratio']
                temp['timestamp'] = miner_data['time']
                temp['name'] = time.strftime("%H:%M", time.localtime(miner_data['time']))
                data.append(temp)
                if i == 0:
                    time_list.append(temp['name'])
            data = sorted(data, key=lambda keys: keys['timestamp'], reverse=False)
            temp_dict['miner_power'] = data[-1]['value']
            temp_dict['power_str'] = format_power(data[-1]['value'])
            temp_dict['data'] = data
            miner_time_list.append(temp_dict)
            i += 1
        return {
            "miner_time_list": miner_time_list,
            "time_list": time_list[::-1],
        }

    @cache_required(cache_key='explorer_power_valid_%s', expire=60 * 60 * 3)
    def get_power_valid(self, page_index, page_size, count, must_update_cache=False):
        '''
        挖矿排行榜-有效算力
        '''
        result = FilfoxBase().get_power_valid(page_index=page_index, page_size=page_size)

        if not result or result.get("statusCode"):
            return {"totalCount": [], "maxQualityAdjPower": [], "totalRawBytePower": 0, "totalQualityAdjPower": 0,
                    "miner_list": []}

        result_dict = dict()
        result_dict['totalCount'] = result['totalCount']  # 总数
        result_dict['maxQualityAdjPower'] = result['maxQualityAdjPower']  # 总数
        result_dict['totalRawBytePower'] = result['totalRawBytePower']  # 总 有效算力
        result_dict['totalQualityAdjPower'] = result['totalQualityAdjPower']  # 总 有效算力
        miner_list = []
        for miner in result['miners']:
            miner_dict = {}
            miner_dict['address'] = miner['address']  # 用户名
            # 标签相关
            if miner.get('tag'):
                miner_dict['tag'] = dict()
                miner_dict['tag']['name'] = miner['tag']['name']  # 标签
                miner_dict['tag']['signed'] = miner['tag']['signed']  # 为true表示账户已完成所有者的签名验证
            miner_dict['rawBytePower'] = miner['rawBytePower']  # 有效算力
            miner_dict['qualityAdjPower'] = format_power(miner['qualityAdjPower'])  # 有效算力
            miner_dict['blocksMined'] = miner['blocksMined']  #
            miner_dict['weightedBlocksMined'] = miner['weightedBlocksMined']  #
            miner_dict['totalRewards'] = round(format_fil_to_decimal(miner['totalRewards']), 2)  # 24小时出块奖励 需要除以18个0
            miner_dict['rewardPerByte'] = miner['rewardPerByte']  #
            miner_dict['rawBytePowerDelta'] = format_power(miner['rawBytePowerDelta'])  # 24h算力增量
            miner_dict['qualityAdjPowerDelta'] = format_power(miner['qualityAdjPowerDelta'])  # 24h算力增量
            # 24h挖矿效率 暂时保留2位小数
            miner_dict['efficient'] = round(float(miner['totalRewards']) / float(
                format_power(miner['rawBytePower'], 'TiB').split(" ")[0]) / (10 ** 18), 2)
            # 占比
            miner_dict['proportion'] = str(
                round(float(miner['rawBytePower']) / float(result['totalRawBytePower']) * 100, 2)) + "%"
            # 地区相关
            if miner.get('location'):
                miner_dict['location'] = dict()
                miner_dict['location']['countryName'] = miner['location']['countryName']  # 国家
                miner_dict['location']['regionName'] = miner['location']['regionName']  # 地区
            miner_list.append(miner_dict)
        if count:
            miner_list = miner_list[:int(count)]
        result_dict['miner_list'] = miner_list
        return result_dict

    @cache_required(cache_key='explorer_blocks_%s', expire=60 * 60 * 3)
    def get_blocks(self, cache_key, page_index, page_size, count, duration="24h", must_update_cache=False):
        '''
        挖矿排行榜-出块
        '''

        result = FilfoxBase().get_blocks_v1(page_size=page_size, page_index=page_index, duration=duration)
        if not result or result.get('totalCount') == 0:
            return {"totalCount": 0, "maxQualityAdjPower": [], "totalRawBytePower": 0, "totalQualityAdjPower": 0,
                    "miner_list": []}

        result_dict = dict()
        result_dict['blockCount'] = result['blockCount']  # 出块总数
        result_dict['height'] = result['height']  # 区块高度
        result_dict['maxWeightedBlocksMined'] = result['maxWeightedBlocksMined']  #
        result_dict['tipsetCount'] = result['tipsetCount']  #
        result_dict['totalCount'] = result['totalCount']  #
        result_dict['totalQualityAdjPower'] = result['totalQualityAdjPower']  #
        result_dict['totalRawBytePower'] = result['totalRawBytePower']  #
        result_dict['totalRewards'] = result['totalRewards']  # 总得奖励数
        result_dict['weightedBlockCount'] = result['weightedBlockCount']  #
        miner_list = []
        for miner in result['miners']:
            miner_dict = {}
            miner_dict['address'] = miner['address']  # 用户名
            # 标签相关
            if miner.get('tag'):
                miner_dict['tag'] = dict()
                miner_dict['tag']['name'] = miner['tag']['name']  # 标签
                miner_dict['tag']['signed'] = miner['tag']['signed']  # 为true表示账户已完成所有者的签名验证

            # 地区相关
            if miner.get('location'):
                miner_dict['location'] = dict()
                miner_dict['location']['countryName'] = miner['location']['countryName']  # 国家
                miner_dict['location']['regionName'] = miner['location']['regionName']  # 地区

            # 其它数据相关
            miner_dict['block_count'] = miner['weightedBlocksMined']  # 出块份数
            miner_dict['luckyValue'] = miner['luckyValue']  # 幸运值
            miner_dict['totalRewards'] = round(format_fil_to_decimal(miner['totalRewards']), 2)  # 出块奖励 需要除以10^18
            # 出块奖励的占比
            miner_dict['proportion'] = str(
                round(float(miner['totalRewards']) / float(result['totalRewards']) * 100, 2)) + "%"
            result_dict['rawBytePower'] = miner['rawBytePower']  # 总 有效算力
            result_dict['qualityAdjPower'] = format_power(miner['qualityAdjPower'])  # 总 有效算力
            miner_list.append(miner_dict)
        if count:
            miner_list = miner_list[:int(count)]
        result_dict['miner_list'] = miner_list
        return result_dict

    @cache_required(cache_key='explorer_power_growth_%s', expire=60 * 60 * 3)
    def get_power_growth(self, cache_key, page_index, page_size, count, duration="24h", must_update_cache=False):
        '''
        挖矿排行榜-算力增速
        '''

        result = FilfoxBase().get_power_increase(page_size=page_size, page_index=page_index, duration=duration)
        if result.get('statusCode'):
            return {"durationPercentage": 0, "height": 0, "maxQualityAdjPowerGrowth": 0, "totalQualityAdjPower": 0,
                    "totalRawBytePower": 0, "totalCount": 0, "miner_list": []}

        result_dict = dict()
        result_dict['durationPercentage'] = result['durationPercentage']  #
        result_dict['height'] = result['height']  #
        result_dict['maxQualityAdjPowerGrowth'] = result['maxQualityAdjPowerGrowth']  #
        result_dict['totalQualityAdjPower'] = result['totalQualityAdjPower']  #
        result_dict['totalRawBytePower'] = result['totalRawBytePower']  #
        result_dict['totalCount'] = result['totalCount']  #
        miner_list = []
        for miner in result['miners']:
            miner_dict = {}
            miner_dict['address'] = miner['address']  # 用户名
            # 标签相关
            if miner.get('tag'):
                miner_dict['tag'] = dict()
                miner_dict['tag']['name'] = miner['tag']['name']  # 标签
                miner_dict['tag']['signed'] = miner['tag']['signed']  # 为true表示账户已完成所有者的签名验证

            # 地区相关
            if miner.get('location'):
                miner_dict['location'] = dict()
                miner_dict['location']['countryName'] = miner['location']['countryName']  # 国家
                miner_dict['location']['regionName'] = miner['location']['regionName']  # 地区

            # 其它数据相关
            miner_dict['rawBytePowerGrowth'] = format_power(miner['rawBytePowerGrowth'])  # 算力增速
            miner_dict['equivalentMiners'] = round(float(miner['equivalentMiners']), 2)  # 矿机当量
            miner_dict['rawBytePowerDelta'] = format_power(miner['rawBytePowerDelta'])  # 算力增量
            miner_dict['rawBytePower'] = format_power(miner['rawBytePower'])  # 有效算力

            # 一个比率
            miner_dict['proportion'] = str(
                round((float(miner['rawBytePowerGrowth']) / float(result['maxQualityAdjPowerGrowth'])) * 100, 4)) + "%"
            miner_list.append(miner_dict)
        if count:
            miner_list = miner_list[:int(count)]

        result_dict['miner_list'] = miner_list
        return result_dict

    @cache_required(cache_key='explorer_tipset_%s', expire=30 * 1)
    def get_tipset(self, page_index, page_size, count, must_update_cache=False):
        result = FilfoxBase().get_tipset_list(page_size=page_size, page_index=page_index)
        if not result or result.get("statusCode"):
            return {"totalCount": 0, "tipsets": []}

        result_tipsets_list = []
        for block in result['tipsets']:
            block_dict = {}
            block_dict['height'] = block['height']  # 高度
            block_dict['messageCount'] = block['messageCount']  # 未知
            block_value_list = []
            for block_value in block['blocks']:
                temp_dict = {}
                temp_dict['cid'] = block_value['cid']  # id
                temp_dict['messageCount'] = block_value['messageCount']  # 消息数
                temp_dict['miner'] = block_value['miner']  # 矿工
                temp_dict['cid'] = block_value['cid']
                # 获取标签
                if block_value.get("minerTag"):
                    temp_dict['minerTag'] = {}
                    temp_dict['minerTag']['name'] = block_value['minerTag']['name']
                    temp_dict['minerTag']['signed'] = block_value['minerTag']['signed']
                else:
                    temp_dict['minerTag'] = None
                temp_dict['reward'] = round(format_fil_to_decimal(block_value.get("reward")), 2) if block_value.get(
                    "reward") else "--"
                block_value_list.append(temp_dict)
            block_dict['block_list'] = block_value_list
            result_tipsets_list.append(block_dict)
        if count:
            result_tipsets_list = result_tipsets_list[:int(count)]

        return {"totalCount": result['totalCount'], "tipsets": result_tipsets_list}

    @cache_required(cache_key='explorer_message_list_%s', expire=30 * 1)
    def get_message_list(self, page_index, page_size, count, must_update_cache=False):
        result = FilfoxBase().get_message_list(page_size=page_size, page_index=page_index)
        if not result or result.get("statusCode"):
            return {"totalCount": 0, "messages_list": [], "methods": []}
        messages_list = []

        for message in result['messages']:
            temp_base_dict = {}
            temp_base_dict['cid'] = message['cid']  # 消息id
            temp_base_dict['from'] = message['from']  # 发送方
            temp_base_dict['to'] = message['to']  # 接收方
            temp_base_dict['timestamp'] = time.strftime("%Y年%m月%d日 %H:%M:%S",
                                                        time.localtime(message['timestamp']))  # 时间
            # 发送方信息
            if message.get("fromTag"):
                temp_base_dict['fromTag'] = {}
                temp_base_dict['fromTag']['name'] = message['fromTag']['name']  # 标签
                temp_base_dict['fromTag']['signed'] = message['fromTag']['signed']  # 是否认证
            # 接收方信息
            if message.get("toTag"):
                temp_base_dict['toTag'] = {}
                temp_base_dict['toTag']['name'] = message['toTag']['name']  # 标签
                temp_base_dict['toTag']['signed'] = message['toTag']['signed']  # 是否认证
            temp_base_dict['height'] = message['height']  # 区块高度
            temp_base_dict['method'] = message['method'] if message.get("method") else "--"  # 方法
            temp_base_dict['value'] = round(format_fil_to_decimal(message['value']), 2)  # 金额
            # 状态?应该是
            if message.get("receipt"):
                temp_base_dict['receipt'] = {}
                temp_base_dict['receipt']['exitCode'] = message['receipt']['exitCode']  # 为0表示正常
            messages_list.append(temp_base_dict)
        if count:
            messages_list = messages_list[:int(count)]

        return {
            "totalCount": result['totalCount'],
            "messages_list": messages_list,
            "methods": result['methods']
        }

    @cache_required(cache_key='explorer_block_statistics', expire=60 * 60)
    def get_block_statistics(self, must_update_cache=False):
        result = FilscanBase().get_block_statistics()
        result_list = []
        result_dict = {"total_block_count": 0, "total_wincount": 0, "total_rewards": 0, "data": result_list}
        if not result or result['result'] is None:
            return result_dict
        result_dict['total_block_count'] = result['result']['total_block_count']  # 出块数
        result_dict['total_wincount'] = result['result']['total_wincount']  # 赢票数
        result_dict['total_rewards'] = result['result']['total_rewards']  # 奖励
        for iter_data in result['result']['data']:
            temp_dict = {
                "blocks": iter_data['blocks'],  # 每小时出块
                "wincount": iter_data['wincount'],  # 每小时赢票
                "rewards": iter_data['rewards'],  # 每小时奖励
                "time": time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime(iter_data['time'])),  # 时间戳,需要转换
            }
            result_list.append(temp_dict)
        return result_dict

    def search(self, value):
        result = FilfoxBase().search(value)
        if not result:
            return format_return(16002, msg="请求失败")
        return format_return(0, data=result)

    @cache_required(cache_key='explorer_block_distribution', expire=60 * 60)
    def get_block_distribution(self):
        result = FilfoxBase().get_block_distribution()
        if not result:
            return None
        result_dict = {
            "otherQualityAdjPower": result['otherQualityAdjPower'],
            "otherRawBytePower": result['otherRawBytePower'],
            "totalQualityAdjPower": result['totalQualityAdjPower'],
            "totalRawBytePower": result['totalRawBytePower'],
        }
        miners_list = []
        for miner in result['miners']:
            temp_dict = {}
            temp_dict['address'] = miner['address']
            temp_dict['rawBytePower'] = format_power(miner['rawBytePower'])
            # 占比
            temp_dict['proportion'] = round(
                (decimal.Decimal(miner['rawBytePower']) / decimal.Decimal(result['totalRawBytePower'])) * 100, 2)
            if miner.get("tag"):
                temp_dict['tag'] = dict()
                temp_dict['tag']['name'] = miner['tag']['name']  # 标签
                temp_dict['tag']['signed'] = miner['tag']['signed']  # 为true表示账户已完成所有者的签名验证
            miners_list.append(temp_dict)
        other_dict = {
            'address': "other",
            'rawBytePower': format_power(result['totalRawBytePower']),
            'proportion': round(
                (decimal.Decimal(result['otherRawBytePower']) / decimal.Decimal(result['totalRawBytePower'])) * 100, 2)
        }
        miners_list.append(other_dict)
        result_dict['miner'] = miners_list
        return result_dict

    @cache_required(cache_key='explorer_block_distribution_%s', expire=60 * 60)
    def get_miner_power_increment_tendency(self, redis_key, count, duration, samples):
        result = FilfoxBase().get_miner_power_increment_tendency(count, duration, samples)
        if not result:
            return []
        result_list = []
        for time_data in result:
            miner_temp_list = []
            temp_dict = {
                "height": time_data['height'],
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_data['timestamp'])),
                "miners": miner_temp_list
            }

            for miner in time_data['miners']:
                temp = {
                    "address": miner['address'],
                    "powerGrowth": format_power(miner['powerGrowth'])
                }
                if miner.get("tag"):
                    temp['tag'] = dict()
                    temp['tag']['name'] = miner['tag']['name']  # 标签
                    temp['tag']['signed'] = miner['tag']['signed']  # 为true表示账户已完成所有者的签名验证
                miner_temp_list.append(temp)
            result_list.append(temp_dict)
        return result_list

    @cache_required(cache_key='explorer_mining_earnings_%s', expire=60 * 60)
    def get_mining_earnings(self, duration):
        result = FilfoxBase().get_mining_earnings(duration)
        if not result:
            return []
        result_list = []
        for data in result:
            temp_dict = {
                "height": data["height"],
                "earnings": round(decimal.Decimal(data["rewardPerByte"]) / decimal.Decimal(315.703555135344972), 4),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data['timestamp'])),
            }
            result_list.append(temp_dict)
        return result_list

    @cache_required(cache_key='explorer_sector_pledge_%s', expire=60 * 60)
    def get_sector_pledge(self, duration):
        result = FilfoxBase().get_sector_pledge(duration)
        if not result:
            return []
        result_list = []
        for data in result:
            temp_dict = {
                "height": data["height"],
                "initialPledge": data["initialPledge"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data['timestamp'])),
            }
            result_list.append(temp_dict)
        return result_list

    @cache_required(cache_key='explorer_gas_tendency_%s', expire=60 * 60)
    def get_gas_tendency(self, redis_key, duration, samples):
        result = FilfoxBase().get_gas_tendency(duration, samples)
        if not result:
            return []
        result_list = []
        for data in result:
            temp_dict = {
                "height": data["height"],
                "baseFee": data["baseFee"],
                "baseFee_str": format_coin_to_str(data["baseFee"]),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data['timestamp'])),
            }
            result_list.append(temp_dict)
        return result_list

    @cache_required(cache_key='explorer_gas_data_24h', expire=60 * 60)
    def get_gas_data_24h(self):
        result = FilfoxBase().get_gas_data_24h()
        if not result:
            return []
        result_list = []
        for all_data in result:
            if all_data['method'] == "":
                sum_value = all_data
                break
        try:
            a = sum_value
        except:
            return []
        for data in result:
            temp_dict = {
                "method": data["method"],
                "count": data["count"],
                "fee": round(format_fil_to_decimal(data["fee"]), 4),
                "gasLimit": int(data["gasLimit"]),
                "gasUsed": int(data["gasUsed"]),
                "gasFeeCap": data["gasFeeCap"],
                "totalFee": round(format_fil_to_decimal(data["totalFee"]), 6),
                "gasPremium": format_coin_to_str(data["gasPremium"], temp_value=1),
                "cost_proportion": round((decimal.Decimal(data["totalFee"]) / decimal.Decimal(a['totalFee'])) * 100, 2),
                "message_proportion": round((decimal.Decimal(data["count"]) / decimal.Decimal(a['count'])) * 100, 2)
            }
            result_list.append(temp_dict)
        return result_list


class ExplorerQueryBase(object):
    """
    根据具体的用户/消息进行查询
    """

    @cache_required(cache_key='explorer_miner_overview_%s', expire=30 * 60)
    def get_miner_overview(self, miner_address):
        result = FilfoxBase().get_miner_overview(miner_address)
        if not result or result.get("statusCode"):
            return None
        result_dict = {}
        # 标签
        # 标签相关
        if result.get('tag'):
            result_dict['tag'] = dict()
            result_dict['tag']['name'] = result['tag']['name']  # 标签
            result_dict['tag']['signed'] = result['tag']['signed']  # 为true表示账户已完成所有者的签名验证
        # 挖矿统计
        if result.get('miningStats'):
            result_dict['miningStats'] = dict()
            result_dict['miningStats']['blocksMined'] = result_dict['miningStats']['blocksMined']  # 出块数量
            result_dict['miningStats']['weightedBlocksMined'] = result_dict['miningStats'][
                'weightedBlocksMined']  # 出块份数
            result_dict['miningStats']['equivalentMiners'] = result_dict['miningStats']['equivalentMiners']  # 矿机当量
            result_dict['miningStats']['luckyValue'] = result_dict['miningStats']['luckyValue']  # 幸运值
            result_dict['miningStats']['totalRewards'] = result_dict['miningStats']['totalRewards']  # 累计出块奖励
        # 矿工概览
        if result.get("balance"):
            result_dict['balance'] = round(format_fil_to_decimal(result['balance']), 2)  # 账户余额-需要除以18个0
        else:
            result_dict['balance'] = 0
        # 账户概览
        if result.get('miner'):
            proportion = decimal.Decimal(result['miner']['qualityAdjPower']) / decimal.Decimal(
                result['miner']['networkQualityAdjPower'])
            result_dict['miner'] = dict()
            result_dict['miner']['peerId'] = result['miner']['peerId']  # 结点id
            result_dict['miner']['sectorSize'] = format_power(result['miner']['sectorSize'])  # 扇区大小
            result_dict['miner']['proportion'] = round(proportion * 100, 2)  # 占比
            result_dict['miner']['qualityAdjPower'] = result['miner']['qualityAdjPower']  # 有效算力
            result_dict['miner']['qualityAdjPower_str'] = format_power(result['miner']['qualityAdjPower'])  # 有效算力
            result_dict['miner']['weightedBlocksMined'] = result['miner']['weightedBlocksMined']  # 累计出块数
            result_dict['miner']['qualityAdjPowerRank'] = result['miner'].get('qualityAdjPowerRank')  # 排名
            result_dict['miner']['totalRewards_all'] = format_fil_to_decimal(result['miner']['totalRewards'],
                                                                             2)  # 累计出块奖励
            result_dict['miner']['pledgeBalance'] = format_fil_to_decimal(result['miner']['sectorPledgeBalance'],
                                                                          2)  # 质押金额
            result_dict['miner']['rawBytePower_str'] = format_power(result['miner']['rawBytePower'])  # 有效算力
            result_dict['miner']['rawBytePower'] = result['miner']['rawBytePower']  # 原值算力
            result_dict['miner']['availableBalance'] = format_fil_to_decimal(
                result['miner']['availableBalance'], 2)  # 可用余额
            # mining_info = self.address_mining_stats(miner_address, duration="24h")
            # result_dict['miner'].update(mining_info)
            if result['miner'].get("sectors"):
                result_dict['miner']['sectors'] = {}
                result_dict['miner']['sectors']['active'] = result['miner']['sectors']['active']
                result_dict['miner']['sectors']['live'] = result['miner']['sectors']['live']
                result_dict['miner']['sectors']['recovering'] = result['miner']['sectors']['recovering']
                result_dict['miner']['sectors']['faulty'] = result['miner']['sectors']['faulty']
            if result['miner'].get("owner"):
                result_dict['miner']['owner'] = {}
                result_dict['miner']['owner']['address'] = result['miner']['owner']['address']
                result_dict['miner']['owner']['balance'] = result['miner']['owner']['balance']
            if result['miner'].get("worker"):
                result_dict['miner']['worker'] = {}
                result_dict['miner']['worker']['address'] = result['miner']['worker']['address']
                result_dict['miner']['worker']['balance'] = result['miner']['worker']['balance']
            if result['miner'].get("location"):
                result_dict['miner']['location'] = result['miner']['location']
            if result['miner'].get("miningStats"):
                result_dict['miner']['miningStats'] = {}
                result_dict['miner']['miningStats']['luckyValue'] = str(
                    round(decimal.Decimal(result['miner']['miningStats']['luckyValue']) * 100, 2)) + "%"  # 幸运值
                result_dict['miner']['miningStats']['equivalentMiners'] = round(
                    decimal.Decimal(result['miner']['miningStats']['equivalentMiners']), 2)  # 矿机当量
                result_dict['miner']['miningStats']['totalRewards'] = \
                    format_fil_to_decimal(result['miner']['miningStats']['totalRewards'], 2)  # 出块奖励
                result_dict['miner']['miningStats']['rawBytePowerDelta'] = result['miner']['miningStats'][
                    'rawBytePowerDelta']  # 出块分数
                result_dict['miner']['miningStats']['weightedBlocksMined'] = result['miner']['miningStats'][
                    'weightedBlocksMined']  # 出块分数
                result_dict['miner']['miningStats']['blocksMined'] = result['miner']['miningStats'][
                    'blocksMined']  # 出块数量
                result_dict['miner']['miningStats']['qualityAdjPowerDelta'] = format_power(
                    result['miner']['miningStats']['qualityAdjPowerDelta'])  # 算力增量
                result_dict['miner']['miningStats']['CalculateForceGrowth'] = format_power(
                    result['miner']['miningStats']['qualityAdjPowerDelta'])  # 算力增速
                # 收益率=总算力/总收益
                if result_dict['miner']['qualityAdjPower'] == "0":
                    efficiency = 0
                else:
                    efficiency = round(
                        float(result_dict['miner']['miningStats']['totalRewards']) /
                        float(format_power_to_TiB(result_dict['miner']['qualityAdjPower']).split(" ")[0]), 4)
                result_dict['efficiency'] = "%.4f" % efficiency

        result_dict['actor'] = result.get('actor')  # 账户权限
        result_dict['robust'] = result.get('robust')  # 地址
        result_dict['id'] = result.get('id')  # minner名称
        result_dict['balance'] = round(format_fil_to_decimal(result['balance']), 2)  # 账户余额
        result_dict['messageCount'] = result.get('messageCount')  # 消息数
        result_dict['createTimestamp'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                                       time.localtime(result['createTimestamp']))  # 创建时间
        result_dict['lastSeenTimestamp'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                                         time.localtime(result['lastSeenTimestamp']))  # 最后登录时间
        return result_dict

    @cache_required(cache_key='explorer_miner_balance_%s', expire=60 * 30)
    def get_miner_address_balance(self, miner_address, detail=False):
        if detail:
            result = FilfoxBase().get_miner_address_balance_stats_detail(miner_address)
        else:
            result = FilfoxBase().get_miner_address_balance_stats(miner_address)

        if not result:
            return []
        result_list = []
        for data in result:
            temp_dict = {}
            temp_dict['availableBalance'] = data.get('availableBalance')  # 可用金额
            # 质押金额
            temp_dict['pledgeBalance'] = int(data.get('sectorPledgeBalance')) if data.get('sectorPledgeBalance') else 0
            temp_dict['balance'] = data['balance']  # 总余额
            temp_dict['time'] = data['timestamp']  # 时间
            temp_dict['height'] = data['height']  # 时间
            # temp_dict['availableBalance'] = round(format_fil_to_decimal(data['availableBalance']), 2)  # 可用金额
            # temp_dict['pledgeBalance'] = round(format_fil_to_decimal(data['pledgeBalance']), 2)  # 质押金额
            # temp_dict['balance'] = round(format_fil_to_decimal(data['balance']), 2)  # 总余额
            # temp_dict['time'] = time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime(data['timestamp']))  # 时间
            result_list.append(temp_dict)
        result_list = sorted(result_list, key=lambda keys: keys['time'])
        return result_list

    @cache_required(cache_key='explorer_miner_stats_%s', expire=60)
    def get_address_power_stats(self, address_id):
        result = FilfoxBase().get_miner_power_stats(address_id)
        if not result or not isinstance(result, list):
            return []
        result_list = []
        for data in result:
            temp_dict = {}
            temp_dict['qualityAdjPower'] = data['qualityAdjPower']  # 有效算力
            temp_dict['qualityAdjPowerDelta'] = data['qualityAdjPowerDelta']  # 有效算力增量
            temp_dict['rawBytePower'] = data['rawBytePower']  # 有效算力
            temp_dict['rawBytePower_data'] = data['rawBytePower']  # 有效算力
            temp_dict['rawBytePowerDelta'] = data['rawBytePowerDelta']  # 有效算力增量
            temp_dict['rawBytePowerDelta_data'] = data['rawBytePowerDelta']  # 有效算力增量
            temp_dict['time'] = data['timestamp']  # 时间
            # temp_dict['qualityAdjPower'] = format_power(data['qualityAdjPower'])  # 有效算力
            # temp_dict['qualityAdjPowerDelta'] = format_power(data['qualityAdjPowerDelta'])  # 有效算力增量
            # temp_dict['rawBytePower'] = format_power(data['rawBytePower'])  # 有效算力
            # temp_dict['rawBytePower_data'] = data['rawBytePower']  # 有效算力
            # temp_dict['rawBytePowerDelta'] = format_power(data['rawBytePowerDelta'])  # 有效算力增量
            # temp_dict['rawBytePowerDelta_data'] = data['rawBytePowerDelta']  # 有效算力增量
            # temp_dict['time'] = time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime(data['timestamp']))  # 时间
            result_list.append(temp_dict)
        return result_list

    @cache_required(cache_key='explorer_mining_stats_%s', expire=60)
    def address_mining_stats(self, miner_address, duration):
        result = FilfoxBase().get_address_mining_stats(miner_address, duration)
        if not result:
            return []
        temp_dict = {}
        temp_dict['luckyValue'] = str(round(decimal.Decimal(result['luckyValue']) * 100, 2)) + "%"  # 幸运值
        temp_dict['equivalentMiners'] = round(decimal.Decimal(result['equivalentMiners']), 2)  # 矿机当量
        temp_dict['totalRewards'] = format_fil_to_decimal(result['totalRewards'], 2)  # 出块奖励
        temp_dict['rawBytePowerDelta'] = result['rawBytePowerDelta']  # 出块分数
        temp_dict['blocksMined'] = result['blocksMined']  # 出块数量
        temp_dict['qualityAdjPowerDelta'] = format_power(result['qualityAdjPowerDelta'])  # 算力增量
        temp_dict['CalculateForceGrowth'] = format_power(result['qualityAdjPowerDelta'])  # 算力增速
        return temp_dict

    def address_message(self, miner_address, page_size, page):
        result = FilfoxBase().get_address_message(miner_address, page_index=page, page_size=page_size)
        if not result:
            return []
        result_list = []
        for message in result['messages']:
            temp_base_dict = {}
            temp_base_dict['cid'] = message['cid']  # 消息id
            temp_base_dict['from'] = message['from']  # 发送方
            temp_base_dict['to'] = message['to']  # 接收方
            temp_base_dict['timestamp'] = time.strftime("%Y年%m月%d日 %H:%M:%S",
                                                        time.localtime(message['timestamp']))  # 时间
            temp_base_dict['height'] = message['height']  # 区块高度
            temp_base_dict['method'] = message['method'] if message.get("method") else "--"  # 方法
            temp_base_dict['value'] = round(format_fil_to_decimal(message['value']), 2)  # 金额
            # 状态?应该是
            if message.get("receipt"):
                temp_base_dict['receipt'] = {}
                temp_base_dict['receipt']['exitCode'] = message['receipt']['exitCode']  # 为0表示正常
            result_list.append(temp_base_dict)
        return {
            "totalCount": result['totalCount'],
            "messages_list": result_list,
            "methods": result['methods']
        }

    @cache_required(cache_key='explorer_block_high_info_%s', expire=60)
    def block_high_info(self, high_value):
        result = FilfoxBase().high_info(high_value)
        if not result:
            return {
                "height": None,
                "messageCount": None,
                "blocks": []
            }
        block_list = []
        for block in result['blocks']:
            temp_dict = {
                "cid": block['cid'],
                "messageCount": block['messageCount'],
                "reward": format_fil_to_decimal(block['reward']),
                "miner": block['miner'],
                "winCount": block['winCount'],
            }
            if block.get('minerTag'):
                temp_dict['minerTag'] = dict()
                temp_dict['minerTag']['name'] = block['minerTag']['name']  # 标签
                temp_dict['minerTag']['signed'] = block['minerTag']['signed']  # 为true表示账户已完成所有者的签名验证
            if block.get('parents'):
                temp_dict['parents'] = block['parents']
            block_list.append(temp_dict)

        return {
            "height": result['height'],
            "messageCount": result['messageCount'],
            "blocks": block_list
        }

    @cache_required(cache_key='explorer_block_id_info_%s', expire=60)
    def block_id_info(self, block_id):
        result = FilfoxBase().block_id_info(block_id)
        if not result:
            return None
        result_dict = {
            "cid": result['cid'],
            "height": result['height'],
            "messageCount": result['messageCount'],
            "miner": result['miner'],
            "parentBaseFee": format_coin_to_str(result['parentBaseFee']),
            "parentStateRoot": result['parentStateRoot'],
            "parentWeight": result['parentWeight'],
            "penalty": format_fil_to_decimal(result['penalty']) if result.get("penalty") else None,
            "reward": format_fil_to_decimal(result['reward']),
            "size": result['size'],
            "winCount": result['winCount'],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result['timestamp']))  # 时间,
        }
        if result.get('parents'):
            result_dict['parents'] = result['parents']

        return result_dict

    def by_block_id_message_list(self, block_id, page_index, page_size):
        result = FilfoxBase().by_block_id_get_message_list(block_id, page_index, page_size)
        if not result:
            return {
                "totalCount": 0,
                "result_list": [],
                "methods": []
            }
        if result.get('statusCode'):
            return {
                "totalCount": 0,
                "result_list": [],
                "methods": []
            }

        result_list = []
        for data in result['messages']:
            temp_dict = {
                "cid": data.get('cid'),
                "from": data.get('from'),
                "method": data.get('method'),
                "to": data.get('to'),
                "value": format_fil_to_decimal(data.get('value')),
            }
            if data.get('fromTag'):
                temp_dict['fromTag'] = dict()
                temp_dict['fromTag']['name'] = data['fromTag']['name']  # 标签
                temp_dict['fromTag']['signed'] = data['fromTag']['signed']  # 为true表示账户已完成所有者的签名验证
            if data.get('toTag'):
                temp_dict['toTag'] = dict()
                temp_dict['toTag']['name'] = data['toTag']['name']  # 标签
                temp_dict['toTag']['signed'] = data['toTag']['signed']  # 为true表示账户已完成所有者的签名验证
            if data.get('receipt'):
                temp_dict['receipt'] = dict()
                temp_dict['receipt']['exitCode'] = data['receipt']['exitCode']  # 标签
            result_list.append(temp_dict)
        return {
            "totalCount": result['totalCount'],
            "result_list": result_list,
            "methods": result['methods']

        }

    def get_message_info_by_message_id(self, message_id):
        result = FilfoxBase().get_message_info_by_message_id(message_id)
        if not result:
            return None
        result_dict = {
            "cid": result['cid'],
            "baseFee": format_float_coin(result['baseFee']),
            "decodedReturnValue": result['decodedReturnValue'] if result.get("decodedReturnValue") else None,
            "from": result['from'],
            "fromActor": result['fromActor'],
            "fromId": result['fromId'],
            "gasFeeCap": format_float_coin(result['gasFeeCap']),
            "gasPremium": format_float_coin(result['gasPremium']),
            "gasLimit": result['gasLimit'],
            "height": result['height'],
            "method": result['method'],
            "methodNumber": result['methodNumber'],
            "params": result['params'],
            "to": result['to'],
            "nonce": result['nonce'],
            "toActor": result['toActor'],
            "toId": result['toId'],
            "version": result['version'],
            "transfers": result['transfers'] if result.get("transfers") else None,
            "value": format_fil_to_decimal(result['value']),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result['timestamp']))
        }
        if result.get("error"):
            result_dict['error'] = result.get("error")
        if result.get('blocks'):
            result_dict['blocks'] = []
            for i in result.get('blocks'):
                result_dict['blocks'].append(i)
        # 参数
        if result.get('decodedParams'):
            result_dict['decodedParams'] = result['decodedParams']
            # result_dict['decodedParams']['DealIds'] = result['decodedParams']['DealIds']  # 标签
            # result_dict['decodedParams']['Expiration'] = result['decodedParams']['Expiration']  # 标签
            # result_dict['decodedParams']['RegisteredProof'] = result['decodedParams']['RegisteredProof']  # 标签
            # result_dict['decodedParams']['ReplaceCapacity'] = result['decodedParams']['ReplaceCapacity']  # 标签
            # result_dict['decodedParams']['ReplaceSector'] = result['decodedParams']['ReplaceSector']  # 标签
            # result_dict['decodedParams']['ReplaceSectorDeadline'] = result['decodedParams'][
            #     'ReplaceSectorDeadline']  # 标签
            # result_dict['decodedParams']['ReplaceSectorPartition'] = result['decodedParams'][
            #     'ReplaceSectorPartition']  # 标签
            # result_dict['decodedParams']['SealedCid'] = result['decodedParams']['SealedCid']  # 标签
            # result_dict['decodedParams']['SealRandEpoch'] = result['decodedParams']['SealRandEpoch']  # 标签
            # result_dict['decodedParams']['SectorNumber'] = result['decodedParams']['SectorNumber']  # 标签
        if result.get('receipt'):
            result_dict['receipt'] = {
                "exitCode": result['receipt']['exitCode'],
                "gasUsed": result['receipt']['gasUsed'],
                "return": result['receipt']['return'],
            }

        return result_dict

    def peer_info(self, peer_id):
        result = FilfoxBase().get_peer_info(peer_id)
        if not result:
            return None
        result_dict = {
            "location": result['location'],
            "multiAddresses": result['multiAddresses'],
            "peerId": result['peerId']
        }
        if result.get('miners'):
            result_dict['miners'] = []
            for i in result.get('miners'):
                result_dict['miners'].append(i)

        return result_dict
