from django.conf.urls import url

from record import views

urlpatterns = [
    url(r'^$', views.price.list_for_display),
    url(r'^price/$', views.price.list_for_display),
    url(r'^account/$', views.account),
    url(r'^contract/$', views.contract),
    # url(r'^usage/(?P<product>\w+)/$', views.usage),
    # url(r'^usage/(?P<product>\w+)/(?P<year>[0-9]{4})/$', views.yearly_usage),
    url(r'^usage/(?P<product_no>\w+)/$', views.usage.usage_list),
    url(r'^usage/(?P<product_no>\w+)/summary/$', views.usage.usage_summary),
    url(r'^usage/(?P<product_no>\w+)/(?P<year>[0-9]{4})/(?P<month>1[0-2]|0[1-9]|[1-9])/$', views.usage.monthly_usage_list),
    url(r'^admin/vms/instance', views.tango_temp_admin),
    url(r'^vms/instance', views.tango_temp),
    url(r'^fee/$', views.fee_list),
    url(r'^fee/summary/$', views.fee_summary),
    url(r'^fee/(?P<product_no>\w+)/$', views.fee_by_prod_range),
    url(r'^fee/(?P<product_no>\w+)/summary/$', views.fee_summary_by_prod_range),
    # url(r'^fee/(?P<year>[0-9]{4})/(?P<month>1[0-2]|0[1-9]|[1-9])/$', views.monthly_fee),
    # url(r'^fee/summary/(?P<product_no>\w+)/(?P<year>[0-9]{4})/(?P<month>1[0-2]|0[1-9]|[1-9])/$', views.monthly_fee),
    # url(r'^fee/(?P<product_no>\w+)/(?P<year>[0-9]{4})/(?P<month>1[0-2]|0[1-9]|[1-9])/$', views.monthly_fee),
]
