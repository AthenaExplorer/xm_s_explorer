from django.conf.urls import url, include

urlpatterns = [
    url(r'^explorer/api/', include('explorer.urls')),
    url(r'^explorer/api/exponent/', include('exponent.urls')),
    url(r'^explorer/api/master_overview/', include('master_overview.urls')),
    url(r'^explorer/api/detail/', include('detail.urls')),
    url(r'^explorer/api/index/', include('fad.urls')),
    url(r'^explorer/api/pro/', include('pro.urls')),
    url(r'^explorer/api/admin/', include('admin.urls')),
]
