import json

from django.shortcuts import render
from django.views.generic import ListView
from django.forms.models import model_to_dict

from views import get_form_models, SkeletonView
from .models import University, UniversityD, UniversityDD
from .forms import * # NOQA
from utils import jsonfy


def startup(request):
    # Set up University* classifiers
    def _rearrange(query_set):
        # use parent parent as key to generate sub-level data
        if len(query_set) == 0:
            return {}

        data = [model_to_dict(ins) for ins in query_set]
        assert 'parent' in data[0], 'Data list has to have parent key'

        reorganised = {}
        for sub in data:
            parent = sub.pop('parent')
            if parent not in reorganised:
                reorganised[parent] = []
            reorganised[parent].append(sub)
        return json.dumps(reorganised)

    level1 = jsonfy(University.objects.all())
    level2 = _rearrange(UniversityD.objects.all())
    level3 = _rearrange(UniversityDD.objects.all())

    form_module_name = __name__.split('.')[0] + '.forms'
    things = [usage for usage in get_form_models(form_module_name) if usage.endswith('usage')]

    return render(request, "startup.html",
                  context={'title': 'Welcome',
                           'things': things,
                           'level1': level1,
                           'level2': level2,
                           'level3': level3})


class ObjectList(SkeletonView, ListView):
    """View class for listing objects"""
    template_name = 'generic_list.html'
    TEMPLATES = {
        'Novausage': 'nova_usage.html',
        'Hpcusage': 'hpc_usage.html'
    }

    def get_template_names(self):
        return self.TEMPLATES.get(self.get_model_name(), self.template_name)
