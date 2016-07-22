from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='bman-index'),
    url(r'^forms/(?P<target>\w+)/$', views.FormsCreateView.as_view(), name='creation-forms'),
    url(r'^forms/(?P<target>\w+)/(?P<id>\w+)/$', views.FormsUpdateView.as_view(), name='update-forms'),
    url(r'^objects/(?P<target>\w+)/$', views.ObjectList.as_view(), name='objects'),
    url(r'^objects/(?P<target>\w+)/(?P<id>\w+)/$', views.ObjectsView.as_view(), name='object'),
    url(r'^api/(?P<target>\w+)/$', views.ApiObjectsView.as_view(), name='api-objects'),
    url(r'^api/(?P<target>\w+)/(?P<id>\w+)/$', views.ApiObjectsView.as_view(), name='api-object'),
    url(r'^api/(?P<target>\w+)/(?P<id>\w+)/(?P<method>\w+)/$', views.ApiObjectsView.as_view(), name='api-object-method'),
]
