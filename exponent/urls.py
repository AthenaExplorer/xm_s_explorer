from django.conf.urls import url

from exponent import views

urlpatterns = [

    # 首页数据

    url(r'get_miner_index$', views.get_miner_index),  # 矿工,综合指数信息
    url(r'get_miner_index_line$', views.get_miner_index_line),  # 矿工综合指数_折线图

    url(r'get_company_index$', views.get_company_index),  # 矿商指数信息
    url(r'get_company_index_line$', views.get_company_index_line),  # 矿商统计类指数信息_折线图

    url(r'get_company_list$', views.get_company_list),  # 获得矿商列表
    url(r'get_miner_to_company_mapping$', views.get_miner_to_company_mapping),  # 获得矿商矿工map关系

    # 排行榜
    url(r'get_miner_ranking$', views.get_miner_ranking),  # 矿工排行榜
    url(r'get_company_ranking$', views.get_company_ranking),  # 矿商排行榜

    # 同步数据定时任务
    url(r'^sync_data_miner$', views.sync_data_miner),  # 矿工
    url(r'^sync_data_miner_company$', views.sync_data_miner_company),  # 综合统计矿工的数据,汇集矿商的数据

]
