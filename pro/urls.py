from django.conf.urls import url

from pro import views

urlpatterns = [

    # 专业版用户
    url(r'^get_pro_user_info$', views.get_pro_user_info),
    url(r'^get_pro_user$', views.get_pro_user),
    url(r'^set_explorer_mobile$', views.set_explorer_mobile),
    url(r'^invite_user$', views.invite_user),
    url(r'^update_pro_tips_flag$', views.update_pro_tips_flag),
    # 节点收藏
    url(r'^get_collectible_miner$', views.get_collectible_miner),
    url(r'^add_collectible_miner$', views.add_collectible_miner),
    url(r'^del_collectible_miner$', views.del_collectible_miner),
    url(r'^get_collectible_miner_list$', views.get_collectible_miner_list),
    # 账户收藏
    url(r'^get_collectible_wallet_address$', views.get_collectible_wallet_address),
    url(r'^add_collectible_wallet_address$', views.add_collectible_wallet_address),
    url(r'^del_collectible_wallet_address$', views.del_collectible_wallet_address),
    url(r'^get_collectible_address_list$', views.get_collectible_address_list),
    url(r'^update_collectible', views.update_collectible),
    url(r'^get_collectible_status$', views.get_collectible_status),  # 判断节点是否收藏
    # 节点监控
    url(r'^get_miner_monitor$', views.get_miner_monitor),
    url(r'^create_update_miner_monitor$', views.create_update_miner_monitor),
    url(r'^del_miner_monitor$', views.del_miner_monitor),

    # 设置报警手机号
    url(r'^get_change_mobile_vercode$', views.get_change_mobile_vercode),
    url(r'^get_warn_mobile$', views.get_warn_mobile),
    url(r'^add_warn_mobile$', views.add_warn_mobile),
    url(r'^set_warn_mobile$', views.set_warn_mobile),
    url(r'^del_warn_mobile$', views.del_warn_mobile),

    # 节点健康度报告
    url(r'^miner_health_report_24h$', views.miner_health_report_24h),
    url(r'^miner_health_report_days$', views.miner_health_report_days),
    url(r'^miner_health_report_wallet_estimated_day$', views.miner_health_report_wallet_estimated_day),
    url(r'^miner_health_report_gas_stat$', views.miner_health_report_gas_stat),
    url(r'^miner_health_report_messages_stat$', views.miner_health_report_messages_stat),
    url(r'^get_miner_health_report_stats$', views.get_miner_health_report_stats),
    # 定时更新数据发送短信
    url(r'^sync_update_miner_monitor$', views.sync_update_miner_monitor),
    url(r'^sync_update_wallet_monitor$', views.sync_update_wallet_monitor),
    # 邀请注册
    url(r'^get_invite_info$', views.get_invite_info),
    url(r'^get_invite_record_list$', views.get_invite_record_list),
    url(r'^get_reward_record_list$', views.get_reward_record_list),

]
