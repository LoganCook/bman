from functools import wraps
import logging
import sys

from django.http import JsonResponse

from utils import get_class_names
from ..models import (TangocloudvmUsage, NectarvmUsage, StorageUsage, HpcUsage, Contact)  # noqa # pylint: disable=unused-import

logger = logging.getLogger(__name__)

_current_module = sys.modules[__name__]


def supported_products():
    # only suport to views if a class in models package has Usage suffix
    return [name.replace('Usage', '') for name
            in get_class_names(__name__.split('.')[0] + '.models')
            if name.endswith('Usage')]


VALID_PRODUCTS = supported_products()


def verify_product_no(func):
    """Verify a prodcut number of view functions before querying database

    If product_no is not in settings.PRODUCT_MAPPER return a 400 error
    and a JSON object {'error': 'Invalid product number'}
    """

    # url_part_to_product_no = lambda string_with_enderscore: string_with_enderscore.replace('_', ' ')

    @wraps(func)
    def wrapper(*args, **kwargs):
        # the first positional argument is request, and the second is product_no
        # kwargs['product_no'] = url_part_to_product_no(kwargs['product_no'])
        kwargs['product_no'] = kwargs['product_no'].capitalize()
        if kwargs['product_no'] in VALID_PRODUCTS:
            return func(*args, **kwargs)
        return JsonResponse({'error': 'Invalid product number'}, status=400)

    return wrapper


def get_usage_class(product_no):
    return getattr(_current_module, product_no.capitalize() + 'Usage')


def get_timestamps_email(request, email_optional=False):
    if email_optional:
        return request.GET['start'], request.GET['end']
    return request.GET['start'], request.GET['end'], request.GET['email']


def convert_qs(qs, fields):
    """Convert a queryset to a JSON array response with selected fields"""
    # return as a JsonResponse with Access-Control-Allow-Origin header
    logger.debug(qs.query)
    return cors_response(JsonResponse(list(qs.values(*fields)), safe=False))


def convert_list(items):
    """Convert a list and return a JsonResponse with Access-Control-Allow-Origin header"""
    return cors_response(JsonResponse(items, safe=False))


def cors_response(response):
    """Add Access-Control-Allow-Origin to response header"""
    response["Access-Control-Allow-Origin"] = "*"
    return response


def unauthorized():
    return cors_response(JsonResponse({'error': 'Unauthorized'}, status=401))
