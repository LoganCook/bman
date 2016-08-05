from django.conf.urls import url
from . import views
from views import JSONView

urlpatterns = [
    url(r'^$', views.startup, name='usage-index'),
    url(r'^objects/(?P<target>\w+)/$', views.ObjectList.as_view(form_mod_name='usage.forms'), name='objects'),
    url(r'^objects/(?P<target>\w+)/(?P<method>\w+)/$', views.ObjectList.as_view(form_mod_name='usage.forms'), name='object-method'),
    url(r'^api/(?P<target>\w+)/$', JSONView.as_view(form_mod_name='usage.forms'), name='api-objects'),
    url(r'^api/(?P<target>\w+)/(?P<method>\w+)/$', JSONView.as_view(form_mod_name='usage.forms'), name='api-object-method'),
]
