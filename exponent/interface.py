from django.db.models import Sum, Avg, Q, Min

from exponent.models import MinerIndex, CompanyMinerIndex, MinerBase, CompanyBase
from xm_s_common.utils import format_power_to_TiB
from xm_s_common import inner_server
import pandas as pd
import numpy as np
from decimal import Decimal
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from xm_s_common import debug, consts, cache, raw_sql
import os
import time

from xm_s_explorer.consts import critical_value
from functools import wraps


def time_get(a_func):
    @wraps(a_func)
    def wrapTheFunction(*args, **kwargs):
        a = time.time()
        result = a_func(*args, **kwargs)
        b = time.time()
        print("函数{}耗时:{}".format(a_func.__name__, str(b - a)))
        return result

    return wrapTheFunction


class IndexQueryBase:
    def get_query_obj(self, model_class, miner_no, miner_type):
        """
        查询单个的数据
        """

        i = 0
        while True:
            if i > 100:
                return None
            date = (datetime.now() - timedelta(days=i)).date()
            queryset = model_class.objects.filter(day=date, miner_no=miner_no, miner_type=miner_type)
            if queryset:
                return queryset
            else:
                i += 1

    def get_query_set(self, model_class, method, miner_type):

        """
        model_class:类名
        method:具体哪项的排名
        查询整体的最新数据
        """
        i = 0
        while True:
            if i > 100:
                return None
            date = (datetime.now() - timedelta(days=i)).date()
            if method == "keep_gas_week_i":
                queryset = eval(
                    "model_class.objects.filter(~Q(keep_gas_week_v=0),~Q(synthesize_rank=None),day='{}',miner_type={}).order_by('-{}')"
                        .format(date, miner_type, method))
            else:
                queryset = eval(
                    "model_class.objects.filter(~Q(synthesize_rank=None),day='{}',miner_type={}).order_by('-{}')".
                        format(date, miner_type, method))
            # queryset = model_class.objects.filter(day=date).order_by()
            if queryset:
                return queryset
            else:
                i += 1

    def get_query_obj_by_company(self, model_class, company_code):
        """
        查询单个的数据
        """
        i = 0
        while True:
            if i > 100:
                return None
            date = (datetime.now() - timedelta(days=i)).date()
            queryset = model_class.objects.filter(day=date, company_code=company_code)
            if queryset:
                return queryset
            else:
                i += 1

    def get_statistics_query_objs(self, model_class, miner_type):
        """
        查询统计类数据
        """
        i = 0
        while True:
            if i > 100:
                return None
            date = (datetime.now() - timedelta(days=i)).date()
            queryset = model_class.objects.filter(day=date, synthesize_rank=None, miner_type=miner_type)
            if queryset:
                return queryset
            else:
                i += 1

    def get_miner_index(self, miner_no, method, miner_type):
        if method == "miner":
            query_obj = self.get_query_obj(MinerIndex, miner_no, miner_type)
            return query_obj if query_obj else None
        elif method == "statistics":
            query_objs = self.get_statistics_query_objs(MinerIndex, miner_type)
            return query_objs

    def get_miner_index_line(self, miner_no, method, start_time, end_time, miner_type):
        if method == "miner":
            query_objs = MinerIndex.objects.filter(
                miner_no=miner_no, day__lte=end_time, day__gte=start_time, miner_type=miner_type
            )
        elif method == "statistics":
            query_objs = MinerIndex.objects.filter(
                synthesize_rank=None, day__lte=end_time, day__gte=start_time, miner_type=miner_type
            )
        else:
            return None
        return query_objs

    def get_company_index(self, company_code, method, miner_type):
        if method == "company":
            query_obj = self.get_query_obj_by_company(CompanyMinerIndex, company_code)
            return query_obj if query_obj else None
        elif method == "statistics":
            query_objs = self.get_statistics_query_objs(CompanyMinerIndex, miner_type)
            return query_objs

    def get_company_index_line(self, company_code, method, start_time, end_time):
        if method == "company":
            query_objs = CompanyMinerIndex.objects.filter(
                company_code=company_code, day__lte=end_time, day__gte=start_time
            )
        elif method == "statistics":
            query_objs = CompanyMinerIndex.objects.filter(
                synthesize_rank=None, day__lte=end_time, day__gte=start_time
            )
        else:
            return None
        return query_objs

    def get_miner_rank(self, index, miner_type):
        objs = self.get_query_set(MinerIndex, index + "_i", miner_type)
        objs = objs[:20] if objs else None
        return objs

    def get_company_rank(self, index, miner_type):
        objs = self.get_query_set(CompanyMinerIndex, index + "_i", miner_type)
        objs = objs[:10] if objs else None
        return objs

    @staticmethod
    def newest_miner(miner_type):
        """
        获得当日人人矿池结点中评分最高的一个节点
        :return:
        """
        try:
            renren_mapping = inner_server.get_company_miner_mapping({"mc_code": "MC_0"}).get("data").get("MC_0")
            miner_list = renren_mapping.get("miners")
            objs = MinerIndex.objects.filter \
                (~Q(synthesize_rank=None), miner_type=miner_type, miner_no__in=miner_list).order_by("-day",
                                                                                                    "synthesize_rank").first().miner_no
            return objs
        except:
            return MinerIndex.objects.filter(~Q(synthesize_rank=None), miner_type=miner_type).order_by(
                "-day").first().miner_no

    @staticmethod
    def newest_company():
        return CompanyMinerIndex.objects.filter(~Q(synthesize_rank=None)).order_by("-day").first().company_code


class IndexBase:

    def get_active_miner_info(self):
        """
        获得当前的活跃矿工,获得其扇区大小之类的基础数据
        :return:{"矿工id":{"详细信息"}}
        """
        result_dict = {}
        i = 1
        while True:
            result = inner_server.get_miner_list({"page_size": 100, "page_index": i})
            # 保存数据
            for miner_info in result['data']['objs']:
                temp_dict = {
                    "join_date": miner_info.get("join_time").split(" ")[0],
                    "miner_no": miner_info.get("miner_no")
                }
                result_dict[miner_info['miner_no']] = temp_dict
            if i >= result['data']["total_page"]:
                break
            else:
                i += 1
        return result_dict

    def get_history_miner_value(self, date):
        """
        获得历史的矿工产出记录
        :param date: 历史数据日期
        :return:
        """
        result_dict = {}
        i = 1
        while True:
            result = inner_server.get_miner_day_records({"page_size": 100, "page_index": i, "date": date})
            # 保存数据
            for miner_info in result['data']['objs']:
                temp_dict = {
                    # 单T奖励
                    "avg_reward_v": Decimal(miner_info.get("avg_reward")),
                    # 总算力=所有扇区*扇区大小
                    "total_power_v": Decimal(miner_info.get("sector_size")) * Decimal(miner_info.get("total_sector")),
                    # 算力增量 = 新增的扇区数*扇区大小
                    "power_increase": Decimal(miner_info.get("new_sector")) * Decimal(miner_info.get("sector_size")),
                    # 生产成本=pre+prove
                    "create_gas": Decimal(miner_info.get("pre_gas")) + Decimal(miner_info.get("prove_gas")),
                    # 维护成本
                    "keep_gas": Decimal(miner_info.get("win_post_gas")),
                    # 扇区累计总数
                    "section_all": int(miner_info.get("total_sector")),
                    # 坏扇区数量
                    "section_fault": int(miner_info.get("faulty_sector")),
                    # 矿工号
                    "miner_no": miner_info.get("miner_no"),
                    # 日期
                    "day": date,
                    # 创建时间
                    "create_time": datetime.now(),
                    # 新增扇区
                    "new_sector": int(miner_info.get("new_sector")),
                    # 当日出块奖励
                    "block_reward": int(miner_info.get("block_reward"))

                }
                result_dict[miner_info['miner_no']] = temp_dict
            if i >= result['data']["total_page"]:
                break
            else:
                i += 1
        return result_dict

    def get_148888_active_miners(self):
        return inner_server.get_148888_active_miners().get("data")

    @time_get
    def get_index_base_value(self, base_df, date, data_type='miner'):
        """
        计算指数评估指标原始值
        :param base_df: 基础数据
        :param date: 日期
        :return:
        """
        data_list = base_df.to_dict(orient="records")
        begin_time = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=6)).date()
        if data_type == 'miner':
            miner_base_objs = MinerBase.objects.filter(day__gte=begin_time)
        else:
            miner_base_objs = CompanyBase.objects.filter(day__gte=begin_time)
        base_seven_df = pd.DataFrame(list(miner_base_objs.values()))
        for data in data_list:
            # 单日算力增长率 = 算力增长/(总算力-算力增长)
            data['day_inc_rate_v'] = Calculate.get_day_inc_rate_v(data)
            # 历史日平均增长率
            data['avg_inc_rate_v'] = Calculate.get_avg_inc_rate_v(data)
            begin_time = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=6)).date()

            # 单日算力增长率 = 算力增长/(总算力-算力增长)
            data['day_inc_rate_v'] = Calculate.get_day_inc_rate_v(data)
            # 历史日平均增长率
            data['avg_inc_rate_v'] = Calculate.get_avg_inc_rate_v(data)
            # 4项7日数据指标
            seven_data_dict = Calculate.get_seven_data(data, begin_time, data_type, base_seven_df)
            data.update(seven_data_dict)

        # begin_time = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=6)).date()
        # # seven_data_dict = Calculate.get_seven_data(data, begin_time, data_type)
        #
        # # 单日算力增长率 = 算力增长/(总算力-算力增长)
        # base_df.loc[:, 'day_inc_rate_v'] = base_df.apply(Calculate.get_day_inc_rate_v, axis=1)
        # # 历史日平均增长率
        # base_df.loc[:, 'avg_inc_rate_v'] = base_df.apply(Calculate.get_avg_inc_rate_v, axis=1)
        # begin_time = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=6)).date()
        # # 七日单T生产成本
        # base_df.loc[:, 'create_gas_week_v'] = base_df.apply(Calculate.get_create_gas_week_v, axis=1,
        #                                                     args=(begin_time, data_type))
        # # 七日单T维护成本
        # base_df.loc[:, 'keep_gas_week_v'] = base_df.apply(Calculate.get_keep_gas_week_v, axis=1,
        #                                                   args=(begin_time, data_type))
        # # 七日错误扇区占比
        # base_df.loc[:, 'section_fault_rate_v'] = base_df.apply(Calculate.get_section_fault_rate_v, axis=1,
        #                                                        args=(begin_time, data_type))
        # 再把这个列表转为df
        result_df = pd.DataFrame(data_list)
        return result_df

    @time_get
    def get_index_base_score(self, index_value_df, date, data_type="miner"):
        """
        计算指数评估指标评分
        :param base_df: 基础数据+每项指标的具体值的数据
        :param date: 日期
        :return:
        #todo  修改说明:异常值不进行删除排名,而是设置为2分
        原始写法:
         # 异常值处理 返回异常值df,无异常值df
        delete_df, index_value_df = self.abnormal_value_delete_avg_reward_v(index_value_df)
        # 计算排名
        Calculate.get_index_by_ranking(index_value_df, "avg_reward_v")  # 单T收益
        # 拼接到一起去
        index_value_df = index_value_df.append(delete_df, ignore_index=True)

        """
        # 获得评分,直接在原本的df上修改,增加一列

        # 异常值处理 返回异常值df,无异常值df
        index_value_df = self.abnormal_value_delete_avg_reward_v(index_value_df)
        # 计算排名
        Calculate.get_index_by_ranking(index_value_df, "avg_reward_v")  # 单T收益
        # # 拼接到一起去
        # index_value_df = index_value_df.append(delete_df, ignore_index=True)

        Calculate.get_index_by_ranking(index_value_df, "total_power_v")  # 总算力

        Calculate.get_index_by_ranking(index_value_df, "day_inc_rate_v")  # 单日算力增长率

        Calculate.get_index_by_ranking(index_value_df, "avg_inc_rate_v")  # 历史日平均增长率

        # delete_df, index_value_df = \
        #     self.abnormal_value_delete_create_gas_week_v(index_value_df, date, data_type=data_type)
        Calculate.get_index_by_ranking(index_value_df, "create_gas_week_v", method='desc')  # 七日单T生产成本
        # index_value_df = index_value_df.append(delete_df, ignore_index=True)

        index_value_df = self.abnormal_value_delete_create_keep_gas_week_v(index_value_df)
        Calculate.get_index_by_ranking(index_value_df, "keep_gas_week_v", method='desc')  # 七日单T维护成本
        # index_value_df = index_value_df.append(delete_df, ignore_index=True)

        Calculate.get_index_by_ranking(index_value_df, "section_fault_rate_v", method='desc')  # 七日错误扇区占比 # 值越小,评分越高

        Calculate.get_index_by_ranking(index_value_df, "power_increment_7day_v")  # 七日错误扇区占比 # 值越小,评分越高

        # 计算7个指数的和
        # index_value_df['synthesize_sum'] = index_value_df[
        #     ['section_fault_rate_i', 'keep_gas_week_i', 'create_gas_week_i',
        #      'avg_inc_rate_i', 'day_inc_rate_i', 'total_power_i',
        #      'avg_reward_i',"power_increment_7day_i"]].sum(axis=1)  #删除 历史日均算力增长,7日维护成本两项
        # 计算总得分,添加权重
        index_value_df['synthesize_sum'] = index_value_df['section_fault_rate_i'] * 2 + \
                                           index_value_df['power_increment_7day_i'] * 1 + \
                                           index_value_df['keep_gas_week_i'] * 2 + \
                                           index_value_df['avg_reward_i'] * 4 + \
                                           index_value_df['total_power_i'] * 4

        # # 获得非异常值的索引 todo  所有项都有评分了(异常值为2),所以不需要删除异常值
        # index = ~index_value_df[
        #     ['section_fault_rate_i', 'keep_gas_week_i', 'total_power_i', 'avg_reward_i',
        #      "power_increment_7day_i"]].isna()
        # # 计算这7个中非0的数量
        # index_value_df['no_zero_count'] = index.astype(int).sum(axis=1)
        # 综合得分
        index_value_df["synthesize_i"] = index_value_df['synthesize_sum'] / 13
        # 对综合评分进行排名
        index_value_df["synthesize_rank"] = index_value_df["synthesize_i"].rank(method='min', ascending=False)
        return index_value_df

    @time_get
    def statistics_miner_value(self, index_score_df, date):
        """
        计算 全网平均,TOP10矿工平均,TOP30矿工平均的指数具体值,指数得分
        top30计算逻辑:
        1.取出总算力前top的miner
        2.分别计算其的真实值(而不是根据二次计算后的指标进行求和)
        3.获得其指标后,根据我们原本的指标,寻找一个距离最近的值进行评分
        """
        # 初始数据截取
        all_df = index_score_df.copy(deep=True)
        top_10_df = index_score_df.sort_values(by='total_power_v', ascending=False).iloc[:10]
        top_30_df = index_score_df.sort_values(by='total_power_v', ascending=False).iloc[:30]

        # 具体的值计算
        all_mean_df = self.get_indicator_synthesize_score(all_df, "基准值", date, index_score_df)
        top_10_df = self.get_indicator_synthesize_score(top_10_df, "TOP10", date, index_score_df)
        top_30_df = self.get_indicator_synthesize_score(top_30_df, "TOP30", date, index_score_df)

        # 写入原本的dataframe中
        index_score_df = index_score_df.append(all_mean_df, ignore_index=True)
        index_score_df = index_score_df.append(top_10_df, ignore_index=True)
        index_score_df = index_score_df.append(top_30_df, ignore_index=True)
        return index_score_df

    def get_indicator_synthesize_score(self, data_df, miner_name, date, all_data_df, data_type='miner'):
        """
        获得综合指标的df,用于加入原本的df,进行表村
        :param data_dict:
        :param all_data_df:所有数据,用于取最值
        :return:
        """
        data_mean_dict = TOPCalculate().get_mean_index(data_df, date, all_data_df, data_type=data_type)
        if data_type == 'miner':
            data_mean_dict.update(
                {"miner_no": miner_name, "day": date, "create_time": datetime.now(), "synthesize_rank": None})
        else:
            data_mean_dict.update(
                {"company_code": miner_name, "day": date, "create_time": datetime.now(),
                 "synthesize_rank": None, "company_name": miner_name})

        # series转为data
        data_mean_df = pd.DataFrame(data_mean_dict, index=[1])
        # 计算综合评分
        # data_mean_df['synthesize_i'] = data_mean_df[['section_fault_rate_i', 'keep_gas_week_i', 'create_gas_week_i',
        #                                              'avg_inc_rate_i', 'day_inc_rate_i', 'total_power_i',
        #                                              'avg_reward_i']].sum(axis=1) / 7
        # todo  这里同样添加了权重系数
        # data_mean_df['synthesize_i'] = data_mean_df[['section_fault_rate_i', 'keep_gas_week_i', 'total_power_i',
        #                                              'avg_reward_i', 'power_increment_7day_i']].sum(axis=1) / 5
        data_mean_df['synthesize_i'] = (data_mean_df['section_fault_rate_i'] * 2 +
                                        data_mean_df['power_increment_7day_i'] * 1 +
                                        data_mean_df['keep_gas_week_i'] * 2 +
                                        data_mean_df['avg_reward_i'] * 4 +
                                        data_mean_df['total_power_i'] * 4) / 13
        return data_mean_df

    def abnormal_value_delete_avg_reward_v(self, index_value_df):
        """
        异常值处理
        对于数据异常的miner_no,删除其排名,并把后面的排名前进
        """
        # 挖矿效率:四分位法
        # 获得异常值索引 Q3+3IQR  大于这部分的需要剔除,挖矿效率为0的也要剔除
        index_value_df.loc[:, 'avg_reward_v'] = index_value_df['avg_reward_v'].astype(np.float)
        describe_series = index_value_df["avg_reward_v"].describe()
        abnormal_limit = (describe_series['75%'] - describe_series['25%']) * 3
        error_index_gt = index_value_df[index_value_df["avg_reward_v"] > describe_series['75%'] + abnormal_limit].index
        error_index_lt = index_value_df[index_value_df["avg_reward_v"] == 0].index
        error_index = list(error_index_gt) + list(error_index_lt)
        # 获取需要删除的部分
        delete_df = index_value_df.loc[error_index]
        # 将异常值部分的得分设置为nan
        index_value_df.loc[error_index, 'avg_reward_i'] = 2
        # # 原始数据删除这一部分
        # index_value_df.drop(error_index, axis=0, inplace=True)
        return index_value_df

    def abnormal_value_delete_create_keep_gas_week_v(self, index_value_df):
        """
        异常值处理
        对于数据异常的miner_no,删除其排名,并把后面的排名前进
        """
        # 维护成本:删除为0的部分
        error_index = index_value_df[index_value_df["avg_reward_v"] == 0].index
        # 获取需要删除的部分
        delete_df = index_value_df.loc[error_index]
        # 将异常值部分的得分设置为nan
        index_value_df.loc[error_index, 'avg_reward_i'] = 2
        # 原始数据删除这一部分
        # index_value_df.drop(error_index, axis=0, inplace=True)
        return index_value_df

    def abnormal_value_delete_create_gas_week_v(self, index_value_df, data_date, data_type="miner"):
        """
        异常值处理
        对于数据异常的miner_no,删除其排名,并把后面的排名前进
        """
        # 7日新增算力成本: 之前7天的新增扇区为0,则该项不计入新增扇区成本评分
        if data_type == "miner":
            miner_list = index_value_df['miner_no'].to_list()
            all_df = None
            for i in range(7):
                date = (datetime.strptime(data_date, "%Y-%m-%d") - timedelta(days=i)).date()
                query_set = MinerBase.objects.filter(day=date, miner_no__in=miner_list)
                if query_set:
                    df = pd.DataFrame(list(query_set.values('miner_no', 'new_sector')))
                    if all_df is not None:
                        all_df = pd.merge(all_df, df, on=['miner_no'])
                    else:
                        all_df = df
            index_value_df = index_value_df.set_index('miner_no')
            all_df = all_df.set_index('miner_no')

        else:
            company_list = index_value_df['company_code'].to_list()
            all_df = None
            for i in range(7):
                date = (datetime.strptime(data_date, "%Y-%m-%d") - timedelta(days=i)).date()
                query_set = CompanyBase.objects.filter(day=date, company_code__in=company_list)
                if query_set:
                    df = pd.DataFrame(list(query_set.values('company_code', 'new_sector')))
                    if all_df is not None:
                        all_df = pd.merge(all_df, df, on=['company_code'])
                    else:
                        all_df = df
            index_value_df = index_value_df.set_index('company_code')
            all_df = all_df.set_index('company_code')

        # 总增加的扇区
        total_sector = all_df.sum(axis=1)
        # 无新增扇区的miner
        zero_df = total_sector[total_sector == 0]
        delete_df = index_value_df.loc[zero_df.index]
        # 有新增扇区的Miner
        no_zero_df = total_sector[total_sector != 0]
        index_value_df = index_value_df.loc[no_zero_df.index]
        delete_df.reset_index(inplace=True)
        index_value_df.reset_index(inplace=True)
        return delete_df, index_value_df

    def sync_data(self, date):
        """
        同步数据主函数
        :param date:
        :return:
        """
        # # # 创建数据库连接
        mysql_info = 'mysql+pymysql://{username}:{passwd}@{host}:{port}/xm_s_explorer?charset=utf8'.format(
            username=os.getenv("MYSQL_ROOT") or 'root', passwd=os.getenv("MYSQL_PASSWORD") or 'hilink888',
            port=os.getenv("MYSQL_PORT") or 3307, host=os.getenv("MYSQL_HOST") or '127.0.0.1'
        )
        con = create_engine(mysql_info)

        # # 1.获得初始数据
        active_miner_info_dict = self.get_active_miner_info()  # 活跃矿工数据
        history_miner_value_dict = self.get_history_miner_value(date)  # 矿工每日数据
        # 2.转为data frame并合并在一起
        # get_148888_active_miners_dict = self.get_148888_active_miners()  # 初始高度处的初始信息

        # # 取出14888高度时初始算力
        # active_miners_148888_df = pd.DataFrame.from_dict(get_148888_active_miners_dict, orient="index").loc[:,
        #                           ['miner_id', "byte_power_value", "byte_power"]].rename(
        #     columns={'miner_id': 'miner_no'})
        active_miner_df = pd.DataFrame.from_dict(active_miner_info_dict, orient="index")
        history_miner_df = pd.DataFrame.from_dict(history_miner_value_dict, orient="index")
        base_df = pd.merge(active_miner_df, history_miner_df, how='inner', on="miner_no")
        # 写入基础数据
        base_df.to_sql(name="exponent_minerbase", con=con, if_exists='append', index=False)
        # base_df.to_csv("data.csv", index=False)
        #
        # base_df = pd.read_csv("data.csv")

        # 分为大矿工和小矿工
        big_miner_df = base_df[base_df["total_power_v"] >= critical_value]
        self.get_index(big_miner_df, date, "big", con)  # 大矿工
        small_miner_df = base_df[base_df["total_power_v"] < critical_value]
        self.get_index(small_miner_df, date, "small", con)  # 小矿工

    def get_index(self, big_miner_df, date, miner_type, con):
        """
        实际上用于进行排名的计算
        :param big_miner_df: 基础数据df
        :param date:
        :param miner_type:  大矿工:big,小矿工:small
        :param con: mysql链接对象
        :return:
        """
        # 计算普通矿工指数评估指标原始值
        index_value_df = self.get_index_base_value(big_miner_df, date)
        # index_value_df.to_csv("value.csv", index=False)
        # index_value_df = pd.read_csv("value.csv")
        # 计算每项指标的得分,综合排名,排名时需要先去除综合排名部分
        index_score_df = self.get_index_base_score(index_value_df, date)
        # 计算其它非真实矿工指数评分,指数原始值
        all_value_df = self.statistics_miner_value(index_score_df, date)

        # 删除不用写入到表中的部分
        all_value_df.drop(["join_date", "synthesize_sum"], inplace=True, axis=1)

        # 删除基础部分数据
        all_value_df.drop(['power_increase', 'create_gas', 'keep_gas', 'section_all', 'section_fault',
                           'new_sector', 'block_reward'], axis=1, inplace=True)
        if miner_type == "big":
            # 添加大矿工标志一列
            all_value_df['miner_type'] = 1
        elif miner_type == "small":
            all_value_df['miner_type'] = 2
        # 写入数据库
        all_value_df.to_sql(name="exponent_minerindex", con=con, if_exists='append', index=False)

    def sync_data_miner_company(self, date):
        # # # 创建数据库连接
        mysql_info = 'mysql+pymysql://{username}:{passwd}@{host}:{port}/xm_s_explorer?charset=utf8'.format(
            username=os.getenv("MYSQL_ROOT") or 'root', passwd=os.getenv("MYSQL_PASSWORD") or 'hilink888',
            port=os.getenv("MYSQL_PORT") or 3307, host=os.getenv("MYSQL_HOST") or '127.0.0.1'
        )
        con = create_engine(mysql_info)

        result = inner_server.get_company_miner_mapping()
        data_dict = result.get("data")
        company_list = []
        for company_code, info in data_dict.items():
            # 矿商基础数据
            company_base_data = CompanyCalculate().get_index_base_value(info.get("miners"), date)
            if not company_base_data.get("join_date"):
                # 如果没有加入时间的,那么不进行计算
                continue
            company_base_data['company_code'] = company_code
            company_base_data['company_name'] = (info.get("name"))
            company_base_data['day'] = date
            CompanyBase.objects.create(**company_base_data)
            company_list.append(company_base_data)
        if not company_list:
            return
        base_df = pd.DataFrame(company_list)
        # base_df.to_csv("company.csv", index=False)
        base_df['join_date'] = base_df['join_date'].apply(lambda x: x.strftime("%Y-%m-%d"))
        # base_df = pd.read_csv("company.csv")
        index_value_df = self.get_index_base_value(base_df, date, data_type='company')
        # 计算每项指标的得分,综合排名,排名时需要先去除综合排名部分
        index_score_df = self.get_index_base_score(index_value_df, date, data_type='company')
        # 计算其它非真实矿工指数评分,指数原始值
        all_value_df = self.statistics_company_value(index_score_df, date, data_type='company')

        # 删除不用写入到表中的部分
        all_value_df.drop(["join_date", "synthesize_sum"], inplace=True, axis=1)

        # 删除基础部分数据
        all_value_df.drop(['power_increase', 'create_gas', 'keep_gas', 'section_all', 'section_fault',
                           'new_sector', 'block_reward'], axis=1, inplace=True)

        all_value_df['create_time'] = datetime.now()
        all_value_df['miner_type'] = 1
        # 写入数据库
        all_value_df.to_sql(name="exponent_companyminerindex", con=con, if_exists='append', index=False)

    def update_company_rank(self, date):
        """
        更新当日的矿商排名信息
        """
        sql = """
        UPDATE exponent_companyminerindex d
            LEFT JOIN (SELECT
            (@rowNO := @rowNo+1) AS rowno,
            id
            FROM (SELECT
            id
            FROM exponent_companyminerindex etr
            WHERE day= "{}"
            ORDER BY etr.synthesize_i DESC) a,
            (SELECT
            @rowNO :=0) b) c
            ON c.id = d.id
            
            SET d.synthesize_rank = rowno
        """.format(date)
        raw_sql.exec_sql(sql)

    def statistics_company_value(self, index_score_df, date, data_type='miner'):
        """
        计算 全网平均,TOP10矿工平均,TOP30矿工平均的指数具体值,指数得分
        """
        # 初始数据截取
        all_df = index_score_df.copy(deep=True)
        top_10_df = index_score_df.sort_values(by='total_power_v', ascending=False).iloc[:10]

        # 具体的值计算
        all_mean_df = self.get_indicator_synthesize_score(all_df, "全网矿商", date, index_score_df, data_type)
        top_10_df = self.get_indicator_synthesize_score(top_10_df, "矿商TOP10", date, index_score_df, data_type)

        # 写入原本的dataframe中
        index_score_df = index_score_df.append(all_mean_df, ignore_index=True)
        index_score_df = index_score_df.append(top_10_df, ignore_index=True)
        return index_score_df


class Calculate:
    @staticmethod
    def get_day_inc_rate_v(series):
        """
        单日算力增长率
        """
        if series['total_power_v'] == Decimal(0):
            return 0
        elif series['total_power_v'] == series['power_increase']:
            return 1
        else:
            return series['power_increase'] / (series['total_power_v'] - series['power_increase'])

    @staticmethod
    def get_avg_inc_rate_v(series):
        """
        计算日均增长率
        """
        power_value = series['total_power_v'] / ((1024 * 1024 * 1024 * 1024) * 100)
        # 间隔的天数
        join_interval = (datetime.strptime(series['day'], "%Y-%m-%d") - datetime.strptime(series['join_date'],
                                                                                          "%Y-%m-%d")).days + 1
        avg_inc_rate_v = pow(Decimal(power_value), 1 / Decimal(join_interval)) - 1
        return avg_inc_rate_v

    @staticmethod
    def get_create_gas_week_v(series, begin_time, data_type="miner"):
        """
        七日单T生产成本
        计算结果为
        """
        if data_type == "miner":
            miner_no = series['miner_no']
            miner_base_objs = MinerBase.objects.filter(
                miner_no=miner_no,
                day__gte=begin_time
            )
        else:
            company_code = series['company_code']
            miner_base_objs = CompanyBase.objects.filter(
                company_code=company_code,
                day__gte=begin_time
            )

        # 总生产成本
        sum_gas = miner_base_objs.aggregate(create_gas=Sum("create_gas"))['create_gas']
        # 总增加的算力 = 新增扇区数*扇区大小/(1024**4)
        sum_power_inc = Decimal(
            miner_base_objs.aggregate(power_increase=Sum("power_increase"))['power_increase'] / (1024 ** 4))
        if float(sum_power_inc) == 0:
            return 0
        # sum(每日的生成成本)/sum(每日增加的算力)
        return sum_gas / sum_power_inc

    @staticmethod
    def get_keep_gas_week_v(series, begin_time, data_type='miner'):
        """
        七日单T维护成本
        计算结果为
        """
        if data_type == "miner":
            miner_no = series['miner_no']
            miner_base_objs = MinerBase.objects.filter(
                miner_no=miner_no,
                day__gte=begin_time
            )
        else:
            company_code = series['company_code']
            miner_base_objs = CompanyBase.objects.filter(
                company_code=company_code,
                day__gte=begin_time
            )
        # 总维护成本
        sum_gas = miner_base_objs.aggregate(keep_gas=Sum("keep_gas"))['keep_gas']
        # 每天的总算力
        sum_power = Decimal(
            miner_base_objs.aggregate(total_power_v=Sum("total_power_v"))['total_power_v'] / (1024 ** 4))
        # sum(每日的维护成本)/sum(每日总算力)
        if int(sum_power) == 0:
            return 0
        return sum_gas / sum_power

    @staticmethod
    def get_section_fault_rate_v(series, begin_time, data_type='miner'):
        """
        七日错误扇区占比
        计算结果为
        """

        if data_type == "miner":
            miner_no = series['miner_no']
            miner_base_objs = MinerBase.objects.filter(
                miner_no=miner_no,
                day__gte=begin_time
            )
        else:
            company_code = series['company_code']
            miner_base_objs = CompanyBase.objects.filter(
                company_code=company_code,
                day__gte=begin_time
            )
        # 每日总扇区
        sum_new_sector = miner_base_objs.aggregate(section_all=Sum("section_all"))['section_all']
        # 每日坏扇区增量
        sum_section_fault = Decimal(
            miner_base_objs.aggregate(section_fault=Sum("section_fault"))['section_fault'])
        if int(sum_new_sector) == 0:
            return 0
        # sum(每日坏扇区增量)/sum(每日总扇区)
        return sum_section_fault / sum_new_sector

    @staticmethod
    def get_score_esc(value, max_value, min_value):
        """
        正向排序,值越大,得分越高
        """
        if Decimal(value) == Decimal(0):
            return 0
        else:
            return 10 - ((max_value - value) / (max_value - min_value)) * 8

    @staticmethod
    def get_score_desc(value, max_value, min_value):
        """
        反向排序,值越大,得分越高
        """
        # print(value, max_value, min_value)
        if Decimal(value) == Decimal(0):
            return 0
        else:
            return 10 - abs((min_value - value) / (max_value - min_value)) * 8

    @staticmethod
    def get_index(index_value_df, columns_name, method="esc"):
        """
        获得指数评分,
        需要删除异常值,总算力指数不需要删除异常值
        :return:
        """
        index_value_df[columns_name] = index_value_df[columns_name].astype(np.float64)
        if not columns_name in ['total_power_v', 'section_fault_rate_v']:
            # # 获得异常值的索引 mean+3*std
            # error_index = index_value_df[
            #     index_value_df[columns_name] > index_value_df[columns_name].mean() + 3 * index_value_df[
            #         columns_name].std()].index
            # 获得异常值索引 Q3+3IQR
            describe_series = index_value_df.describe()[columns_name]
            abnormal_limit = (describe_series['75%'] - describe_series['25%']) * 3
            error_index = index_value_df[index_value_df[columns_name] > abnormal_limit].index
            # 获取需要删除的部分
            delete_df = index_value_df.loc[error_index]
            # 删除异常值部分
            index_value_df.drop(error_index, inplace=True)
        # 打印需要处理的一列的信息
        print(index_value_df.describe()[columns_name])
        # 然后可以评分的计算
        index_columns_name = columns_name.rsplit("_", 1)[0] + "_i"
        if method == "esc":
            index_value_df[index_columns_name] = index_value_df[columns_name]. \
                apply(Calculate.get_score_esc, args=(index_value_df[columns_name].max(),
                                                     index_value_df[columns_name].min())).astype(float)
        else:
            index_value_df[index_columns_name] = index_value_df[columns_name]. \
                apply(Calculate.get_score_desc, args=(index_value_df[columns_name].max(),
                                                      index_value_df[columns_name].min())).astype(float)
        if not columns_name in ['total_power_v', 'section_fault_rate_v']:
            # 将异常值部分放进去
            index_value_df = index_value_df.append(delete_df)
            # 将异常值的评分设置为10
            values = {columns_name: 10}
            index_value_df.fillna(value=values, inplace=True)

    @staticmethod
    def get_index_by_ranking(index_value_df, columns_name, method="esc"):
        """
        根据排名,获得这一项的评分
        """
        # 将当前处理的这一列数据转为float
        index_value_df.loc[:, columns_name] = index_value_df[columns_name].astype(np.float64)
        # 异常值处理

        # 获得这一列的排序
        if method == "esc":
            index_value_df.loc[:, columns_name + "ranking"] = index_value_df[columns_name].rank(method='min',
                                                                                                ascending=False)
        else:
            index_value_df.loc[:, columns_name + "ranking"] = index_value_df[columns_name].rank(method='min',
                                                                                                ascending=True)
        # 获得评分
        index_columns_name = columns_name.rsplit("_", 1)[0] + "_i"
        index_value_df.loc[:, index_columns_name] = (1 - index_value_df[columns_name + "ranking"] / index_value_df[
            columns_name + "ranking"].max()) * 8 + 2
        index_value_df.drop([columns_name + "ranking"], inplace=True, axis=1)

    @staticmethod
    def get_statistics_index(value, data_df, col_name):
        """
        对于综合型数据,获得其指数的值,选择距离当前值最靠近的一个指数的值
        :value:综合性指数的值
        :col_name: 列名
        :return:
        """
        data_df["temp"] = abs(data_df[col_name].astype(np.float) - float(value))
        try:
            data_index = data_df["temp"].idxmin()
        except:
            data_index = data_df["temp"].astype(np.float64).idxmin()
        index_columns_name = col_name.rsplit("_", 1)[0] + "_i"
        data_df.drop("temp", inplace=True, axis=1)
        return data_df.loc[data_index, index_columns_name]

    @staticmethod
    def get_seven_data(data, begin_time, data_type, base_seven_df):

        if data_type == "miner":
            miner_no = data['miner_no']
            # miner_base_objs = MinerBase.objects.filter(miner_no=miner_no, day__gte=begin_time)
            miner_df = base_seven_df[base_seven_df['miner_no'] == miner_no]
        else:
            company_code = data['company_code']
            # miner_base_objs = CompanyBase.objects.filter(company_code=company_code,day__gte=begin_time)
            miner_df = base_seven_df[base_seven_df['company_code'] == company_code]
        result_dict = dict()

        # 总生产成本
        sum_gas = miner_df["create_gas"].sum()
        # 总增加的算力 = 新增扇区数*扇区大小/(1024**4)
        sum_power_inc = miner_df["power_increase"].sum() / (1024 ** 4)
        if float(sum_power_inc) == 0:
            result_dict['create_gas_week_v'] = 0
        else:
            # sum(每日的生成成本)/sum(每日增加的算力)
            result_dict['create_gas_week_v'] = sum_gas / sum_power_inc  # 七日单T生产成本

        # 每天的总算力
        sum_power = miner_df["total_power_v"].sum() / (1024 ** 4)

        sum_keep_gas = miner_df["keep_gas"].sum()
        # sum(每日的维护成本)/sum(每日总算力)
        if int(sum_power) == 0:
            result_dict['keep_gas_week_v'] = 0
        else:
            result_dict['keep_gas_week_v'] = sum_keep_gas / sum_power  # 七日单T维护成本

        # 每日总扇区
        sum_new_sector = miner_df["section_all"].sum()
        # 每日坏扇区增量
        sum_section_fault = miner_df["section_fault"].sum()
        if int(sum_new_sector) == 0:
            result_dict['section_fault_rate_v'] = 0
        else:
            # sum(每日坏扇区增量)/sum(每日总扇区)
            result_dict['section_fault_rate_v'] = sum_section_fault / sum_new_sector  # 七日错误扇区占比

        # 7日算力平均增量  获得日期最大的天数,日期最小的天数  计算两个天数的差值得到数据天数,然后计算算力增量
        # 如果只有一条数据,那么算力增量为0?
        max_df = miner_df[miner_df['day'] == miner_df['day'].max()]
        min_df = miner_df[miner_df['day'] == miner_df['day'].min()]
        day = (max_df['day'].values[0] - min_df['day'].values[0]).days
        if day == 0:
            result_dict['power_increment_7day_v'] = 0
        else:
            power_day_add = (max_df['total_power_v'].values[0] - min_df['total_power_v'].values[0]) / day  # 7日平均算力增量
            result_dict['power_increment_7day_v'] = round(power_day_add)

        return result_dict


class TOPCalculate:
    """
    用于编写计算综合排名(top10,top30)的方法
    """

    def get_mean_index(self, data_frame, date, all_data_df, data_type="miner"):
        """
        获得综合性数据的具体指数评分
        :all_data_df:所有数据的df,用于取最值
        :return:
        """
        data_frame['block_reward'] = data_frame['block_reward'].astype(np.float64)
        count = data_frame.shape[0]  # 总数据条数
        if data_type == "miner":
            obj_list = data_frame['miner_no'].to_list()
            temp_df = data_frame.drop(["join_date", 'miner_no', 'create_time', 'day'], axis=1)
        else:
            obj_list = data_frame['company_code'].to_list()
            temp_df = data_frame.drop(["join_date", 'company_code', 'day', "company_name"], axis=1)

        # 获得合并后总值
        merge_dict = temp_df.sum(axis=0).astype(np.float64).to_dict()
        result_dict = dict()

        # 计算指数评估指标原始值
        # 总算力
        result_dict['total_power_v'] = merge_dict['total_power_v'] / count
        # 单t收益=总爆块奖励/总算力
        result_dict['avg_reward_v'] = merge_dict['block_reward'] / (merge_dict['total_power_v'] / (1024 ** 4)) / (
                10 ** 18)
        # 单日算力增长率 = 算力增长/(总算力-算力增长)
        result_dict['day_inc_rate_v'] = self.get_day_inc_rate_v(merge_dict)
        # 历史日平均增长率
        result_dict['avg_inc_rate_v'] = merge_dict['avg_inc_rate_v'] / count
        begin_time = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=6)).date()
        # 七日单T生产成本
        result_dict['create_gas_week_v'] = float(
            self.get_create_gas_week_v(merge_dict, begin_time, obj_list, data_type))
        # 七日单T维护成本
        result_dict['keep_gas_week_v'] = float(self.get_keep_gas_week_v(merge_dict, begin_time, obj_list, data_type))
        # 七日错误扇区占比
        result_dict['section_fault_rate_v'] = float(
            self.get_section_fault_rate_v(merge_dict, begin_time, obj_list, data_type))
        # 七日算力增量
        result_dict['power_increment_7day_v'] = float(
            self.power_increment_7day_i(merge_dict, begin_time, obj_list, data_type))

        # 计算指数
        # 统计类型数据计算指数,在其他数据中找到一个最相近的值,使用其的指数
        # 总算力
        result_dict['total_power_i'] = Calculate.get_statistics_index(result_dict['total_power_v'], all_data_df,
                                                                      "total_power_v")
        # 单t收益=总爆块奖励/总算力
        result_dict['avg_reward_i'] = Calculate.get_statistics_index(result_dict['avg_reward_v'], all_data_df,
                                                                     "avg_reward_v")
        # 单日算力增长率 = 算力增长/(总算力-算力增长)
        result_dict['day_inc_rate_i'] = Calculate.get_statistics_index(result_dict['day_inc_rate_v'], all_data_df,
                                                                       "day_inc_rate_v")
        # 历史日平均增长率
        result_dict['avg_inc_rate_i'] = Calculate.get_statistics_index(result_dict['avg_inc_rate_v'], all_data_df,
                                                                       "avg_inc_rate_v")
        # 七日单T生产成本
        result_dict['create_gas_week_i'] = Calculate.get_statistics_index(result_dict['create_gas_week_v'], all_data_df,
                                                                          "create_gas_week_v")
        # 七日单T维护成本
        result_dict['keep_gas_week_i'] = Calculate.get_statistics_index(result_dict['keep_gas_week_v'], all_data_df,
                                                                        "keep_gas_week_v")
        # 七日错误扇区占比
        result_dict['section_fault_rate_i'] = Calculate.get_statistics_index(result_dict['section_fault_rate_v'],
                                                                             all_data_df, "section_fault_rate_v")
        # 七日算力平均增量
        result_dict['power_increment_7day_i'] = Calculate.get_statistics_index(result_dict['power_increment_7day_v'],
                                                                               all_data_df, "power_increment_7day_v")

        return result_dict

    @staticmethod
    def get_day_inc_rate_v(series):
        """
        单日算力增长率
        """
        if series['total_power_v'] == series['power_increase']:
            return 1
        else:
            return series['power_increase'] / (series['total_power_v'] - series['power_increase'])

    @staticmethod
    def get_create_gas_week_v(series, begin_time, miner_list, data_type):
        """
        七日单T生产成本
        计算结果为
        """
        if data_type == "miner":
            miner_base_objs = MinerBase.objects.filter(
                miner_no__in=miner_list,
                day__gte=begin_time
            )
        else:
            miner_base_objs = CompanyBase.objects.filter(
                company_code__in=miner_list,
                day__gte=begin_time
            )

        # 总生产成本
        sum_gas = miner_base_objs.aggregate(create_gas=Sum("create_gas"))['create_gas']
        # 总增加的算力
        sum_power_inc = Decimal(
            miner_base_objs.aggregate(power_increase=Sum("power_increase"))['power_increase'] / (1024 ** 4))
        if int(sum_power_inc) == 0:
            return 0
        # sum(每日的生成成本)/sum(每日增加的算力)
        return sum_gas / sum_power_inc

    @staticmethod
    def get_keep_gas_week_v(series, begin_time, miner_list, data_type='miner'):
        """
        七日单T维护成本
        计算结果为
        """
        if data_type == "miner":
            miner_base_objs = MinerBase.objects.filter(
                miner_no__in=miner_list,
                day__gte=begin_time
            )
        else:
            miner_base_objs = CompanyBase.objects.filter(
                company_code__in=miner_list,
                day__gte=begin_time
            )
        # 总维护成本
        sum_gas = miner_base_objs.aggregate(keep_gas=Sum("keep_gas"))['keep_gas']
        # 每天的总算力
        sum_power = Decimal(
            miner_base_objs.aggregate(total_power_v=Sum("total_power_v"))['total_power_v'] / (1024 ** 4))
        # sum(每日的维护成本)/sum(每日总算力)
        if int(sum_power) == 0:
            return 0
        return sum_gas / sum_power

    @staticmethod
    def get_section_fault_rate_v(series, begin_time, miner_list, data_type="miner"):
        """
        七日错误扇区占比
        计算结果为
        """
        if data_type == "miner":
            miner_base_objs = MinerBase.objects.filter(
                miner_no__in=miner_list,
                day__gte=begin_time
            )
        else:
            miner_base_objs = CompanyBase.objects.filter(
                company_code__in=miner_list,
                day__gte=begin_time
            )
        # 每日总扇区增量
        sum_new_sector = miner_base_objs.aggregate(section_all=Sum("section_all"))['section_all']
        # 每日坏扇区增量
        sum_section_fault = Decimal(
            miner_base_objs.aggregate(section_fault=Sum("section_fault"))['section_fault'])
        if int(sum_new_sector) == 0:
            return 0
        # sum(每日坏扇区增量)/sum(每日总扇区增量)
        return sum_section_fault / sum_new_sector

    @staticmethod
    def power_increment_7day_i(series, begin_time, miner_list, data_type="miner"):
        """
        七日算力增量
        计算结果为
        如果仅7日都没有数据,那么今日算力总量为算力增量
        """
        count = 7
        if data_type == "miner":
            miner_base_start_objs = MinerBase.objects.filter(
                miner_no__in=miner_list,
                day=begin_time
            )
            if not miner_base_start_objs:
                for i in range(6):
                    miner_base_start_objs = MinerBase.objects.filter(
                        miner_no__in=miner_list,
                        day=begin_time + timedelta(days=i + 1)
                    )
                    count -= 1
                    if miner_base_start_objs:
                        break

            miner_base_end_objs = MinerBase.objects.filter(
                miner_no__in=miner_list,
                day=begin_time + timedelta(days=6)  # 查询今天的数据
            )
        else:
            miner_base_start_objs = CompanyBase.objects.filter(
                company_code__in=miner_list,
                day=begin_time
            )
            if not miner_base_start_objs:
                for i in range(6):
                    miner_base_start_objs = CompanyBase.objects.filter(
                        company_code__in=miner_list,
                        day=begin_time + timedelta(days=i + 1)
                    )
                    count -= 1
                    if miner_base_start_objs:
                        break
            miner_base_end_objs = CompanyBase.objects.filter(
                company_code__in=miner_list,
                day=begin_time + timedelta(days=6)
            )

        start_power = miner_base_start_objs.aggregate(sum=Sum("total_power_v"))['sum']
        if not start_power:
            start_power = 0
        end_power = miner_base_end_objs.aggregate(sum=Sum("total_power_v"))['sum']
        return end_power - start_power / count


class CompanyCalculate:
    def get_index_base_value(self, miner_list, date):
        result_dict = {}
        query_set = MinerBase.objects.filter(miner_no__in=miner_list, day=date)
        result_dict['total_power_v'] = query_set.aggregate(value=Sum("total_power_v"))['value']  # 总算力
        try:
            result_dict['avg_reward_v'] = \
                query_set.aggregate(value=Sum("block_reward"))['value'] / (
                        result_dict['total_power_v'] / (1024 ** 4)) / (
                        10 ** 18)
        except:
            result_dict['avg_reward_v'] = Decimal(0)
        result_dict['power_increase'] = query_set.aggregate(value=Sum("power_increase"))['value']  # 算力增长
        result_dict['create_gas'] = query_set.aggregate(value=Sum("create_gas"))['value']  # 生产成本
        result_dict['keep_gas'] = query_set.aggregate(value=Sum("keep_gas"))['value']  # 维护成本
        result_dict['section_all'] = query_set.aggregate(value=Sum("section_all"))['value']  # 扇区累计总数
        result_dict['section_fault'] = query_set.aggregate(value=Sum("section_fault"))['value']  # 坏扇区数量
        result_dict['new_sector'] = query_set.aggregate(value=Sum("new_sector"))['value']  # 新增扇区
        result_dict['block_reward'] = query_set.aggregate(value=Sum("block_reward"))['value']  # 单日出块奖励
        result_dict['join_date'] = query_set.aggregate(value=Min("join_date"))['value']  # 加入时间
        for key, value in result_dict.items():
            if result_dict[key] is None:
                result_dict[key] = Decimal(0)
        return result_dict
