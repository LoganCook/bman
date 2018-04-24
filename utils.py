import sys
import json
import inspect

import django.db
from django.forms.models import model_to_dict


def repack(j_string):
    """Repack a result of serializers.serialize json string
    by removing model field, move pk and all fields in fields into
    a dict and return the result of json.dumps.
    """
    serialized = json.loads(j_string)
    if len(serialized) == 0:
        return json.dumps([])

    assert 'pk' in serialized[0] and 'model' in serialized[0], \
        'Not a serialized model'

    size = len(serialized)
    data = [None] * size
    for i in range(size):
        data[i] = serialized[i]['fields']
        data[i]['pk'] = serialized[i]['pk']
    return json.dumps(data)


def _generator(data):
    # local model class method return dict through to_dict for
    # complex data with extend linked data, not just ids
    if hasattr(data, 'to_dict'):
        converted = data.to_dict()
    elif isinstance(data, django.db.models.Model):
        converted = model_to_dict(data)
    else:
        converted = data
    return converted


def jsonfy(data):
    """Converts data to be sent in JSON"""

    # query can retrun
    # 1. a model instance
    # 2. QuerySet, which is an iterator of model instances
    # 3. ValueQuerySet, which is an iterator of dicts
    # 4. list of things, likely some Python types
    converted = {}
    if isinstance(data, django.db.models.query.ValuesQuerySet):
        converted = list(data)
    elif isinstance(data, django.db.models.QuerySet):
        converted = [_generator(d) for d in data]
    elif isinstance(data, django.db.models.Model):
        converted = _generator(data)
    elif isinstance(data, list):
        converted = [_generator(d) for d in data]
    else:
        # might be a base Python type
        converted = data
    # it may still fail, let the call to deal with exceptions
    return json.dumps(converted)


def list_to_dict(list_of_dict, key_name, value_names=None):
    """Convert a list of dict to a dict

    value of key_name of each object is the key of the new dict
    and the object is the value. key_name is kept. If the key_name
    cannot be found, the entry is skiped, no error is raised.
    value_names: is a list for filtering in.
    """
    # TODO: make dynamicsp/views.py use this function instead of its own
    dic = {}
    if value_names:
        for elem in list_of_dict:
            if key_name in elem:
                dic[elem[key_name]] = {k: v for (k, v) in elem.items() if k in value_names}
    else:
        for elem in list_of_dict:
            if key_name in elem:
                dic[elem[key_name]] = elem
    return dic


def dict_to_object(dic):
    """
    Convert a dictionary into an object so its values can be accessed by getattr
    """
    # https://docs.python.org/3/tutorial/classes.html
    class DataObject:  # pylint: disable=R0903
        pass
    obj = DataObject()
    for key, value in dic.items():
        setattr(obj, key, value)
    return obj


def get_class_names(module_name):
    """Get a list of class names loaded into a module"""
    # Currently used in creating a white list of classes which can be shown through views
    return [name for name, obj in inspect.getmembers(sys.modules[module_name])
            if inspect.isclass(obj)]
