import string, random,datetime
from django.db.models import Sum
from pro.models import CollectibleMiner, CollectibleWalletAddress,ProUser,InviteRecord,RewardRecord,WarnMobile
from xm_s_common import inner_server
from xm_s_common.utils import _d,format_fil_to_decimal
from xm_s_common.third.binghe_sdk import BingheEsBase
from django.db import transaction

class ProBase(object):
    @classmethod
    def get_collectible_miners(cls, user_id):
        return CollectibleMiner.objects.filter(user_id=user_id).all()

    @classmethod
    def get_collectible_address(cls, user_id):
        return CollectibleWalletAddress.objects.filter(user_id=user_id).all()

    @classmethod
    def get_collectible_status(cls, user_id, c_id, collectible_type):
        if collectible_type == "wallet":
            return CollectibleWalletAddress.objects.filter(user_id=user_id, wallet_address=c_id).exists()
        if collectible_type == "miner":
            return CollectibleMiner.objects.filter(user_id=user_id, miner_no=c_id).exists()

    @classmethod
    def update_collectible(cls, user_id, c_id, collectible_type, remarks):
        if collectible_type == "wallet":
            return CollectibleWalletAddress.objects.filter(user_id=user_id, wallet_address=c_id).update(remarks=remarks)
        if collectible_type == "miner":
            return CollectibleMiner.objects.filter(user_id=user_id, miner_no=c_id).update(remarks=remarks)

    @classmethod
    def avg_reward_percentage_score(cls, miner_value, overview_vale):
        """系统综合评分的产出效率：百分比计算方案"""
        # 产出效率
        # 非常高效：高于全网均值30 %
        # 优秀：高于全网均值30 % 以内
        # 中等：低于全网均值30 %
        # 低效：低于全网均值30 % 以上
        score = "I1"
        mark = ""
        if miner_value >= overview_vale:
            per = round((miner_value - overview_vale) / overview_vale, 2)
            mark = "高于全网均值{}".format(per)
            if per >= 0.3:
                score = "I2"
            else:
                score = "I1"
        if miner_value < overview_vale:
            per = round((overview_vale - miner_value) / overview_vale, 2)
            mark = "低于于全网均值{}".format(per)
            if per <= 0.3:
                score = "I3"
            else:
                score = "I4"
        return score, per

    @classmethod
    def cost_percentage_score(cls, miner_value, overview_vale):
        """系统综合评分的新增算力成本：百分比计算方案"""
        # 新增算力成本
        # 非常低：低于全网均值10 % 以上
        # 低：低于全网均值10 % 以内
        # 中等：高于全网均值10 % 以内
        # 高：高于全网均值10 % 以上
        score = "C1"
        mark = ""
        if miner_value < overview_vale:
            per = round((overview_vale - miner_value) / overview_vale, 2)
            mark = "低于于全网均值{}".format(per)
            if per >= 0.1:
                score = "C1"
            else:
                score = "C2"
        if miner_value >= overview_vale:
            per = round((miner_value - overview_vale) / overview_vale, 2)
            mark = "高于全网均值{}".format(per)
            if per <= 0.1:
                score = "C3"
            else:
                score = "C4"
        return score, per

    @classmethod
    def get_score_content(cls, score):
        """
        获取评分的内容
        :param score:
        :return:
        """
        # 评分
        score_dict = {"S1": ["1", 20], "S2": ["2", 10], "S3": ["3", 0],  # 运行状态
                      "I1": ["1", 22], "I2": ["2", 20], "I3": ["3", 10], "I4": ["4", 0],  # 产出效率
                      "C1": ["1", 22], "C2": ["2", 20], "C3": ["3", 10], "C4": ["4", 0],  # 新增算力成本
                      "CS1": ["1", 10], "CS2": ["2", 0],  # 成本分析
                      "W1": ["1", 10], "W2": ["2", 0],  # 爆块分析
                      "WA1": ["1", 8], "WA2": ["2", 8], "WA3": ["3", 0]  # 钱包分析
                      }
        return score_dict[score]

    @classmethod
    def get_miner_monitor_value(cls, miner_no, warn_method):
        """
        获取节点的监控具体值
        :param miner_no:
        :param warn_method:
        :return:
        """
        miner_result = inner_server.get_miner_health_report_24h_by_no({"miner_no": miner_no}).get("data", {})
        create_gas = format_fil_to_decimal(miner_result.get("create_gas", 0),4)
        sector_size = miner_result.get("sector_size")
        avg_reward = format_fil_to_decimal(miner_result.get("avg_reward"), 4)

        result_dict = inner_server.get_overview_stat().get("data", {})  # 概览
        overview_avg_reward = format_fil_to_decimal(result_dict.get("avg_reward"), 4)  # 全网产出效率
        overview_pledge = format_fil_to_decimal(result_dict.get("avg_pledge"), 4)  # 全网单T质押
        overview_create_gas_32 = format_fil_to_decimal(result_dict.get("create_gas_32"), 4)  # 全网32生成成本
        overview_create_gas_64 = format_fil_to_decimal(result_dict.get("create_gas_64"), 4)  # 全网单体质押
        overview_create_gas = overview_create_gas_32 if sector_size == "32.00 GiB" else overview_create_gas_64
        result = {}
        if warn_method == "create_gas":  # 算力成本监控
            result = dict(overview_pledge=overview_pledge, miner_value_overview=overview_create_gas,
                          miner_value=create_gas, sector_size=sector_size[:2]+" GiB")
        if warn_method == "avg_reward":  # 产出效率
            result = dict(miner_value_overview=overview_avg_reward, miner_value=avg_reward)
        if warn_method == "sector_faulty":  # 扇区监控
            result = dict(total_sector=miner_result["total_sector"], active_sector=miner_result["active_sector"],
                          faulty_sector=miner_result["faulty_sector"],
                          recovering_sector=miner_result["recovering_sector"])
        return result

    @classmethod
    def get_wallet_address_value(cls, wallet_address, wallet_type):
        """
        获取钱包监控具体值
        :param wallet_address:
        :param wallet_type:
        :return:
        """
        # 这里必须是存储节点的矿工 相关地址
        result = inner_server.get_wallet_info({"id_or_address": wallet_address})
        # result = BingheEsBase().get_miner_wallet_value(wallet_address)
        if result.get("code") != 0:
            return {}
        balance = result.get("data").get("value", 0)
        return dict(balance=_d(balance), wallet_type=wallet_type)

    @classmethod
    def get_invite_info(cls, user_id):
        """
        获取邀请信息
        :param user_id:
        :return:
        """
        user = cls.create_invite_code(user_id)
        result = {"invite_code": user.invite_code,"invite_count":user.invite_count,"reward_count":user.reward_count}
        return result

    @classmethod
    def create_invite_code(cls, user_id):
        """
        获取邀请信息
        :param user_id:
        :return:
        """

        user = ProUser.objects.filter(user_id=user_id).first()
        if not user.invite_code:
            flag = True
            while flag:
                invite_code = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
                try:
                    user.invite_code = invite_code
                    user.save()
                    flag = False
                except Exception as e:
                    print(e)
        return user

    @classmethod
    def create_pro_user(cls, user_id):
        """
        创建其他来源的用户自动创建浏览器用户信息
        :param user_id:
        :return:
        """
        user_info = inner_server.get_user_profile(user_id=user_id)
        if user_info:
            obj, created = ProUser.objects.update_or_create(user_id=user_id, defaults=dict(
                mobile=user_info["mobile"], user_create_time=user_info['create_time'], app_id=user_info.get('app_id')
            ))
            if not WarnMobile.objects.filter(user_id=obj.user_id).exists():
                WarnMobile(user_id=obj.user_id, mobile=obj.mobile).save()
            return obj, created
        return None, None

    @classmethod
    @transaction.atomic
    def cal_invite_pro_time(cls, invite_code):
        # 統計是否满足3次满足就发奖励
        invites = InviteRecord.objects.filter(invite_code=invite_code, status=False).all()
        last = 0
        for i in range(len(invites)//3):
            for invite in invites[last:(i+1) * 3]:
                invite.status = True
                invite.save()
            last = (i+1) * 3
            RewardRecord(invite_code=invite_code, reward=1).save()
            user = ProUser.objects.filter(invite_code=invite_code).first()
            if not user.is_pro:
                user.is_pro = True
                user.expire_time = datetime.datetime.now() + datetime.timedelta(days=30)
            else:
                if user.expire_time:
                    if user.expire_time < datetime.datetime.now():
                        user.expire_time = datetime.datetime.now() + datetime.timedelta(days=30)
                    else:
                        user.expire_time = user.expire_time + datetime.timedelta(days=30)
            user.save()
        # 统计数据
        invite_count = InviteRecord.objects.filter(invite_code=invite_code).count()
        reward_count = RewardRecord.objects.filter(invite_code=invite_code).aggregate(reward_count=Sum('reward'))[
                                "reward_count"] or 0
        ProUser.objects.filter(invite_code=invite_code).update(invite_count=invite_count, reward_count=reward_count)