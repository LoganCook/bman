from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.startup, name='service-index'),
    # url(r'^Organisation$', views.get_tops, name='nectar'),
    # url(r'^nectar$', views.get_nectar, name='get_top_orgs'),
    url(r'^(?i)api/organisation/$', views.Organisations.as_view(), name='api-orgs'),
    url(r'^(?i)api/organisation/(?P<id>[-\w]+)/$', views.Organisation.as_view(), name='api-object'),  # to get organisation itself
    url(r'^(?i)api/organisation/(?P<id>[-\w]+)/(?P<method>\w+)/$', views.Organisation.as_view(), name='api-object-method'),
    # below are for admin
    url(r'^(?i)api/v2/contract/(?P<name>\w+)/$', views.Contract.as_view(), name='api-contract'),  # For accessing any Orders
    url(r'^(?i)api/access/$', views.Access.as_view(), name='api-access'),  # eRSA account, HPC - work around
    url(r'^(?i)api/ersaaccount/$', views.ERSAAccount.as_view(), name='api-account'),  # eRSA account, HPC
    url(r'^(?i)api/tangocompute/$', views.TangoCompute.as_view(), name='api-tango-compute'),  # Tango HPC
    url(r'^(?i)api/anzsrc-for/$', views.ANZSRCFor.as_view(), name='api-anzsrc-for'),  # ANZSRC-FOR codes of orders
    url(r'^(?i)api/rdsreport/$', views.RDSReport.as_view(), name='api-rds-report'),  # Order information for RDS report
]
