from xm_s_common.third.binghe_sdk import BingheEsBase


class DetailBase:
    def get_line(self, data_type, miner_no, start_time, end_time):
        result = BingheEsBase().get_line(data_type, miner_no, start_time, end_time)
        if result:
            result_data = []
            result_list = result.get("hits")
            for data in result_list:
                result_data.append(data.get("_source"))
            return result_data
        else:
            return []
