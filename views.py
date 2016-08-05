import sys
import inspect

from django.views.generic import View
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse, HttpResponseBadRequest, Http404)

from utils import jsonfy


def get_classes(module_name):
    """Get a list of classes in a module"""
    # Currently used in creating a white list of form class which can be shown throgh generic view
    classes = []
    for name, obj in inspect.getmembers(sys.modules[module_name]):
        if inspect.isclass(obj) and obj.__module__ == module_name:
            classes.append(name)
    return classes


def get_form_models(module_name):
    """Get a list of models in a module for display"""
    return [_form_to_model(thing) for thing in get_classes(module_name)]


# Utility functions to convert to and from XXXForm class names to Model names
def _form_to_model(fullname):
    return fullname.lower().replace('form', '').capitalize()


def _nomalise_form_name(target):
    return target.capitalize() + 'Form'


# This is for very generic views for quick development
class SkeletonView(View):
    """
    Base skeleton view based on some built-in criteria with general methods for mixins

    SkeletonView has two ways to get data:
     1. get_object: has keyword id, single instance
     2. get_queryset: either from a model or a class method of model

    keywords in url are in kwargs, query string arguments are in filters.
    """
    # Only models have form can be interacted with
    form_mod_name = ''
    form_class = None

    def dispatch(self, request, *args, **kwargs):
        # request url is in this format with all parts optional:
        # /target/(id)?/(method)?/?arg1=one&arg2=two
        # Save parsed query string into self.filters for function calls.
        self.filters = {}
        # when a function expecting a list and client only provided one,
        # that function only needs to do a dumy split like this:
        # arg.split(';')
        for k, v in request.GET.lists():
            if len(v) == 1:
                self.filters[k] = v[0]
            else:
                self.filters[k] = v

        to_be_loaded = _nomalise_form_name(self.kwargs.pop('target'))
        print("Dispatch method called from %s for : %s" % (self.__class__.__name__, to_be_loaded))
        allowed_classess = get_classes(self.form_mod_name)
        if to_be_loaded in allowed_classess:
            self.form_class = getattr(sys.modules[self.form_mod_name], to_be_loaded)
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseBadRequest("Bad request - out of range")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = context['object_name'] = _form_to_model(self.form_class.__name__)
        context['opts'] = self.kwargs
        return context

    def get_object(self):
        """Works like SingleObjectMixin but not using slug_field, slug_url_kwarg, pk_url_kwarg"""
        # https://github.com/django/django/blob/master/django/views/generic/detail.py#L22
        instance = None
        obj_id = self.kwargs.get('id', None)
        if obj_id is None:
            # Never should be here
            raise RuntimeError("No id, check code and url config")

        query_target = self.form_class.Meta.model
        try:
            instance = query_target.objects.get(pk=obj_id)
        except query_target.DoesNotExist:
            raise Http404("Object does not exist")
        return instance

    def get_queryset(self):
        # Used in ListView, or any views query for multiple instances
        query_target = self.form_class.Meta.model
        if 'method' in self.kwargs:
            method = self.kwargs.pop('method')
            # class mothod of model can return either QuerySet and its
            # derived classes like ValuesQuerySet or list
            qs = getattr(query_target, method)(**self.filters)
        else:
            qs = query_target.objects.all().filter(**self.filters)
        return qs

    def get_success_url(self):
        target = _form_to_model(self.form_class.__name__)
        return reverse('objects', kwargs={'target': target})

    def get_model_name(self):
        return _form_to_model(self.form_class.__name__)


# Might worth to check if HttpRequest.is_ajax()
# RESTful url design pattern:
# http://blog.mwaysolutions.com/2014/06/05/10-best-practices-for-better-restful-api/
class JSONView(SkeletonView):
    """View for calls on api end points in JSON"""
    def get(self, request, *args, **kwargs):
        if 'id' in self.kwargs:
            qr = self.get_object()
        else:
            qr = self.get_queryset()
        data = jsonfy(qr)

        # Clients are likely running on other servers, so we
        # have to allow CROS access otherwise retrun directly
        # return HttpResponse(data,  content_type="application/json")
        response = HttpResponse(data, content_type="application/json")
        # Origin can be limited once orgins are known
        response["Access-Control-Allow-Origin"] = "*"
        # Other options are not used but kept here for record
        # response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        # response["Access-Control-Max-Age"] = "1000"
        # response["Access-Control-Allow-Headers"] = "*"
        return response
