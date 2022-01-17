from django.conf.urls import url

from master_overview import views

urlpatterns = [
    # 数据部分
    url(r'^get_overview$', views.get_overview),  # 全网信息
    url(r'^get_overview_day_records$', views.get_overview_day_records),  # 历史信息4个走势图
    url(r'^get_miner_list_by_raw_power$', views.get_miner_list_by_raw_power),  # 矿工信息-有效算力排行榜
    url(r'^get_miner_list_by_power_inc$', views.get_miner_list_by_power_inc),  # 矿工信息-算力增速排行榜
    url(r'^get_miner_list_by_block$', views.get_miner_list_by_block),  # 矿工信息-出块数排行榜
    url(r'^get_miner_list_by_avg_reward$', views.get_miner_list_by_avg_reward),  # 矿工信息-参数效率排行榜
    # gas费
    url(r'^get_base_fee_trends$', views.get_base_fee_trends),  # 24小时gas费
    url(r'^get_gas_stat_all$', views.get_gas_stat_all),  # gas费统计
    url(r'^get_gas_cost_stat$', views.get_gas_cost_stat),  # gas费统计

    # 区块
    url(r'^get_tipsets$', views.get_tipsets),  # 获得区块

    # 消息
    url(r'^get_message_list$', views.get_message_list),  # 获得消息列表

    # 内存池  修改一下 为了可以提交
    url(r'^get_memory_pool_message$', views.get_memory_pool_message),  # 内存池消息列表

    url('^search_miner_or_wallet$', views.search_miner_or_wallet),  # 判断地址类型 存储矿工or  钱包矿工
    url('^search$', views.search),  # 首页搜索按钮
    url('^search_miner_type$', views.search_miner_type),  # 查询矿工类型,post/worker/owner/miner
    # url('^get_miner_tag$', views.get_miner_tag),  # 获得所有标签
    url('^sync_miner_tag$', views.sync_miner_tag),  # 同步所有矿工的标签

    # 申领标签
    url('^get_miner_apply_tag$', views.get_miner_apply_tag),  # 获取申领标签
    url('^set_miner_apply_tag$', views.set_miner_apply_tag),  # 设置申领标签
    url('^miner_tag_classify$', views.miner_tag_classify),  # 矿工标签分类
    url(r'^get_tag_status$', views.get_tag_status),
]
