from django.conf.urls import url

from admin import views

urlpatterns = [

    # 专业版用户管理
    url(r'^get_pro_user_list$', views.get_pro_user_list),
    url(r'^add_pro_user$', views.add_pro_user),
    url(r'^update_pro_user$', views.update_pro_user),
    url(r'^get_invite_user_list$', views.get_invite_user_list),
    url(r'^get_invite_info_list$', views.get_invite_info_list),
    # 管理Admin
    url(r'^get_admin_user_info$', views.get_admin_user_info),
    url(r'^create_admin_user$', views.create_admin_user),
    url(r'^get_admin_user_list$', views.get_admin_user_list),
    # 渠道来源管理
    url(r'^get_user_source_list$', views.get_user_source_list),
    url(r'^create_user_source$', views.create_user_source),
    url(r'^update_user_source$', views.update_user_source),
    # 标签管理
    url(r'^get_miner_apply_tag_list$', views.get_miner_apply_tag_list),
    url(r'^update_miner_apply_tag$', views.update_miner_apply_tag),
    url(r'^update_tag_status$', views.update_tag_status),
]
