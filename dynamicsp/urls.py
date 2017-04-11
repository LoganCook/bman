from django.conf.urls import url
from . import views

# I don't do magic mapping: all services have to be explicitly stated.
urlpatterns = [
    url(r'^$', views.startup, name='service-index'),
    # url(r'^Organisation$', views.get_tops, name='nectar'),
    # url(r'^nectar$', views.get_nectar, name='get_top_orgs'),
    url(r'^(?i)api/organisation/$', views.Organisations.as_view(), name='api-orgs'),  # this should support table list for all of services and Account, Contact?
    url(r'^(?i)api/organisation/(?P<id>[-\w]+)/$', views.Organisation.as_view(), name='api-object'),  # to get organisation itself
    url(r'^(?i)api/organisation/(?P<id>[-\w]+)/(?P<method>\w+)/$', views.Organisation.as_view(), name='api-object-method'),
    # below are for admin
    url(r'^(?i)api/nectar/$', views.Nectar.as_view(), name='api-nectar'),
    url(r'^(?i)api/rds/$', views.RDS.as_view(), name='api-rds'),  # RDS Allocation
    url(r'^(?i)api/rdsbackup/$', views.RDSBackup.as_view(), name='api-rds-backup'),  # RDS Backup Allocation
    url(r'^(?i)api/access/$', views.Access.as_view(), name='api-access'),  # eRSA account, HPC
    url(r'^(?i)api/anzsrc-for/$', views.ANZSRCFor.as_view(), name='api-anzsrc-for'),  # ANZSRC-FOR codes of orders
    url(r'^(?i)api/rdsreport/$', views.RDSReport.as_view(), name='api-rds-report'),  # Order information for RDS report
]
