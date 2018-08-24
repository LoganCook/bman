from functools import wraps
import logging
import sys
import re

from django.http import JsonResponse

from utils import get_class_names
from ..models import (TangocloudvmUsage, NectarvmUsage, StorageUsage, HpcUsage, Contact)  # noqa # pylint: disable=unused-import


logger = logging.getLogger(__name__)

_current_module = sys.modules[__name__]


def supported_products():
    # only suport to views if a class in models package has Usage suffix
    # these names known to outside as product_no, should not be
    # confused as product number in product catalogue in CRM
    return [name.replace('Usage', '') for name
            in get_class_names(__name__.split('.')[0] + '.models')
            if name.endswith('Usage')]


VALID_PRODUCTS = supported_products()


def verify_product_no(func):
    """Verify a prodcut_no of view functions before querying database

    If product_no is not in settings.PRODUCT_MAPPER return a 400 error
    and a JSON object {'error': 'Invalid product_no'}
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # the first positional argument is request, and the rest are item generated
        # by django: e.g. product_no
        kwargs['product_no'] = kwargs['product_no'].capitalize()
        if kwargs['product_no'] in VALID_PRODUCTS:
            return func(*args, **kwargs)
        return JsonResponse({'error': 'Invalid product number'}, status=400)

    return wrapper


def require_valid_email(func):
    """Check if a request has a valid email address linked to known user or admin

    If failed, it returns a 401
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            Contact.get_by_email(args[0].GET['email'])
        except Contact.DoesNotExist:
            return unauthorized()

        return func(*args, **kwargs)

    return wrapper


def check_required_query_args(required_args):
    """Check if required query args present

    If failed, it returns a 400 error and a JSON object
    {'error': 'Missing required query args: blar'}
    """
    def outer(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for required_arg in required_args:
                if required_arg not in args[0].GET:
                    return JsonResponse({'error': 'Missing required query arg: %s' % required_arg}, status=400)
            return func(*args, **kwargs)

        return wrapper
    return outer


def verify_bearer_header(func):
    """Verify if a request has Authorization header, type is Bearer"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]
        if 'HTTP_AUTHORIZATION' in request.META \
                and request.META['HTTP_AUTHORIZATION'].startswith('Bearer'):
            return func(*args, **kwargs)
        return unauthorized()

    return wrapper


AUTHORIZATION_BEARER = re.compile('^Bearer ([^ \t\n\r\f\v]+)$')


def extract_access_token(request):
    """Extract access_token from Authorization header"""
    if 'HTTP_AUTHORIZATION' in request.META:
        authorization_header = AUTHORIZATION_BEARER.match(request.META['HTTP_AUTHORIZATION'])
        if authorization_header:
            return authorization_header.group(1)
    return None


def get_usage_class(product_no):
    """Get a usage class by product_no

    Some product_no has only one product, some has more

    :param str product_no: symbol known to outside of a product
    or a family of product, internally, name of usage class without Usage suffix
    """
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
