import json

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
