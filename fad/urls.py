"""ind URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from myapp import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from otherapp.views import Home
    2. Add a URL to urlpatterns:  path('', Home.asview(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url

from .views import get_details, latitude_score, get_score, get_height \
    , alter_baseline, cal_scores, price, sub_dimension_switch, alter_factor, alter_scale, time_at_0, time_at_8, \
    add_basic_score_and_weighting_score, record_main_dime, get_height_msg

urlpatterns = [
    # 总览接口和FIL综合指数接口
    url(r'^details', get_details),
    url(r'^scores', get_score),
    # FIL分项维度指数接口
    url(r'^latitude_score', latitude_score),

    # 修改基线系数接口 （一次性修改全部的）
    url(r'^alter_baseline$', alter_baseline),
    # 修改权重系数接口（可以修改一个,需要传入id和修改后的值）
    url(r'^alter_factor$', alter_factor),
    # 修改综合指数得分接口 4:4:2(必须一次性修改全部)
    url(r'^sxale$', alter_scale),
    # # 删除子维度接口（设置isactive=0，需要传入id和switch，switch的参数为0,1（0关闭，1启动））
    url(r'^switcher$', sub_dimension_switch),

    # 定时任务
    url(r'^update0$', time_at_0),  # 5,6,7,9,16,19,20,21,22,24
    url(r'^update8$', time_at_8),  # 8,11,12,10,15,23

    # 以下接口不对外使用
    # 获取ES里高度数据
    url(r'^get_binghe_es_data', get_height),
    url(r'^get_height_msg', get_height_msg),
    # 计算基础系数
    url(r'^cal$', cal_scores),
    # 数据丢失后补基础数据
    url(r'^cali$', add_basic_score_and_weighting_score),
    # 计算主维度得分
    url(r'^rmd$', record_main_dime),

    url(r'^p', price),
]
