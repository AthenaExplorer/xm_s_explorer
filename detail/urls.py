from django.conf.urls import url, include
from detail import views

urlpatterns = [
    url(r'^get_tipset_by_height$', views.get_tipset_by_height),  # 区块高度详情
    url(r'^get_message_detail$', views.get_message_detail),  # 消息详情
    url(r'^get_block_by_cid$', views.get_tipset_by_block_cid),  # 消息详情
    url(r'^get_block_message$', views.get_block_message),  # 消息详情

    # 矿工相关
    url(r'^get_miner_overview_by_no$', views.get_miner_overview_by_no),  # 矿工概览
    url(r'^get_miner_gas_by_no$', views.get_miner_gas_by_no),  # 矿工gas消耗对比图7/30/90
    url(r'^get_miner_day_gas_list_by_no$', views.get_miner_day_gas_list_by_no),  # 矿工gas消耗列表
    url(r'^get_miner_line_chart_by_no$', views.get_miner_line_chart_by_no),  # 矿工折线图,三个折线图一个接口
    url(r'^get_calculate_block_and_reward$', views.get_calculate_block_and_reward),  # 预测出块奖励
    url(r'^get_transfer_list_by_no$', views.get_transfer_list_by_no),  # 获得用户的转账列表
    url(r'^get_message_list$', views.get_message_list),  # 获得用户消息列表
    url(r'^get_miner_blocks$', views.get_miner_blocks),  # 获得用户出块列表
    url(r'^get_miner_wallet_line_chart_by_no$', views.get_miner_wallet_line_chart_by_no),  # 获得用户出块列表
    url(r'^get_miner_mining_stats_by_no$', views.get_miner_mining_stats_by_no),  # 产出统计
    url(r'^get_deal_list$', views.get_deal_list),  # 订单列表
    url(r'^get_deal_info$', views.get_deal_info),  # 订单详情
]
