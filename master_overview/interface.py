from master_overview.models import MinerApplyTag
# from master_overview.serializer import MinerTagSerializer
from xm_s_common.utils import format_es_fil_data
from xm_s_common.third.other_sdk import RRMine
from xm_s_common.decorator import cache_required
from xm_s_common.third.binghe_sdk import BingheEsBase
from xm_s_common import raw_sql
from django.db.models import Q
from master_overview.common import tag_calssify


class OverViewBase:
    def search_type(self, value):
        # 判断是否中文,如果是中文就直接返回
        for str_data in value:
            if '\u4e00' <= str_data <= '\u9fff':
                return
        # 判断是否为矿工
        result = BingheEsBase().get_is_miner(value)
        if result.get("hits"):
            return {"address": value, "type": "address"}
        # 判断是否为区块高度
        if value.isdigit():
            result = BingheEsBase().get_is_block_hight(value)
            if result.get("hits"):
                return {"address": value, "type": "tipset"}
        # 判断是否为区块id
        result = BingheEsBase().get_is_block(value)
        if result.get("hits"):
            return {"address": value, "type": "block"}
        # 判断是否为消息id
        result = BingheEsBase().get_is_message(value)
        if result.get("hits"):
            return {"address": value, "type": "message"}

    def search_miner_or_wallet(self, value):
        # 判断是否为矿工
        result = BingheEsBase().get_is_miner_owner(value)
        if result.get("hits"):
            return {"address": value, "type": "shot"}
        # 判断是否为矿工
        result = BingheEsBase().get_is_miner_wallet(value)
        if result.get("hits"):
            return {"address": value, "type": "wallet"}

    def search_miner_type(self, value):
        result = BingheEsBase().get_is_miner(value, index="chainwatch-atpool_miner")
        if not result.get("hits"):
            result = BingheEsBase().get_is_miner(value)
        if not result.get("hits"):
            return
        else:
            fields = ["miner_id", "address", "owner_id", "worker_id", "owner_address", "post_address",
                      "worker_address", "poster_id"]
            data = result.get("hits")[0].get("_source")
            # 查询钱包余额
            wallet_info = BingheEsBase().get_pool_miner_wallet_detail(miner_no=data.get("miner_id"))

            for field in fields:
                if data.get(field) == value:
                    if wallet_info.get("hits"):
                        data.update(wallet_info.get("hits")[0].get("_source"))
                        data = format_es_fil_data(data)
                    return {"type": field, "obj": data}

    # @cache_required("miner_tag_", expire=60 * 60 * 6, )
    # def get_miner_tag(self, must_update_cache=False):
    #     objs = MinerTag.objects.filter()
    #     serializer = MinerTagSerializer(objs, many=True)
    #     return serializer.data

    def get_miner_tag_by_miner(self, miner_no_list=[]):
        objs = MinerApplyTag.objects.filter(status=True)
        if miner_no_list:
            objs = objs.filter(Q(miner_no__in=miner_no_list) | Q(address__in=miner_no_list))
        return objs

    @cache_required("rr_fil_overview", expire=60 * 5)
    def rr_fil_overview(self, must_update_cache=False):
        rr_api_result = RRMine().get_fil_overview()
        return rr_api_result.get("datas")

    @cache_required("miner_tag_classify", expire=60 * 5)
    def miner_tag_classify(self):
        """
        矿工标签分类
        :return:
        """
        # #  先用笨办法解决,后面可能考虑一个分词器类型框架
        # sql = '''
        #     SELECT GROUP_CONCAT(miner_no),
        #     GROUP_CONCAT(signed),en_tag
        #     FROM master_overview_minerapplytag
        #     WHERE status = 1
        #     GROUP BY en_tag
        # '''
        # result = {}
        # data = raw_sql.exec_sql(sql)
        # dict_data = {a[2]: a for a in data}
        # for tag_str in tag_calssify:
        #     for row in data:
        #         if row[2].find(tag_str) > -1:
        #             result.setdefault(tag_str, [])
        #             result[tag_str].extend([{"miner_no": a[0], "signed":a[1], "en_tag":row[2]} for a in zip(row[0].split(","), row[1].split(","))])
        #             dict_data.pop(row[2], None)
        # # 没有统一标记数据
        # for key, value in dict_data.items():
        #     result[key]=[{"miner_no": a[0], "signed": a[1], "en_tag": value[2]} for a in zip(value[0].split(","), value[1].split(","))]
        # return result

