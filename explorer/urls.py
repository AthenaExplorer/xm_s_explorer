from django.conf.urls import url

from explorer import views

urlpatterns = [
    # 首页
    url(r'^get_block_chart$', views.get_block_chart),  # 爆块信息统计
    url(r'^get_overview$', views.get_overview),  # 概览
    url(r'^get_hashrate_ranking$', views.get_hashrate_ranking),  # 算力走势-有效算力
    url(r'^get_power_valid$', views.get_power_valid),  # 矿工排行榜-有效算力
    url(r'^get_blocks$', views.get_blocks),  # 矿工排行榜-出块数
    url(r'^get_power_growth$', views.get_power_growth),  # 矿工排行榜-算力增速
    url(r'^get_tipset$', views.get_tipset),  # 最新区块列表
    url(r'^get_message_list$', views.get_message_list),  # 消息列表
    url(r'^get_block_statistics$', views.get_block_statistics),  # 出块统计
    # 首页点击事件

    # 矿工查询(矿工id)
    url(r'^address/(?P<address_id>.*?)/overview$', views.address_overview),  # 账户信息_概览 判断是普通用户还是管理用户  根据miner字段判断
    url(r'^address/(?P<address_id>.*?)/balance$', views.address_balance),  # 账户信息_账户钱包变化
    url(r'^address/(?P<address_id>.*?)/power-stats$', views.address_power_stats),  # 账户信息_算力变化(根据miner查询)
    url(r'^address/(?P<address_id>.*?)/message$', views.address_message),  # 账户信息_消息列表
    # url(r'^address/(?P<address_id>.*?)/power-overview$', views.address_power_overview),  # 账户信息_算力概览
    url(r'^address/(?P<address_id>.*?)/mining_stats$', views.address_mining_stats),  # 账户信息_算力概览(内部调用,不需要使用)

    # 根据区块高度查询
    url(r'^block_high/(?P<high_value>.*?)/block_high_info$', views.block_high_info),  # 区块高度详情
    url(r'^block/(?P<block_id>.*?)/block_info$', views.block_id_info),  # 区块详情
    url(r'^block/(?P<block_id>.*?)/block_message_list$', views.by_block_id_message_list),  # 区块消息列表

    # 消息搜索
    url(r'^message/(?P<message_id>.*?)/message_info$', views.message_info_by_message_id),  # 区块高度详情

    # 节点搜索
    url(r'^peer/(?P<peer_id>.*?)/peer_info$', views.peer_info),  # 节点详情
    url('^search$', views.search),  # 首页搜索按钮

    # 统计---挖矿图表
    url(r'^get_block_distribution$', views.get_block_distribution),  # 矿工有效算力分布
    url(r'^get_mining_earnings$', views.get_mining_earnings),  # 挖矿收益
    url(r'^get_sector_pledge$', views.get_sector_pledge),  # 挖矿收益
    url(r'^get_miner_power_increment_tendency$', views.get_miner_power_increment_tendency),  # 矿工算力增量走势

    # 统计---gas统计
    url(r'^get_gas_tendency$', views.get_gas_tendency),  # gas走势
    url(r'^get_gas_data_24h$', views.get_gas_data_24h),  # 24小时gas数据

    # 长地址转短地址
    url(r'^address_to_miner_no&', views.address_to_miner_no)
]
