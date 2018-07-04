import logging

from date_helpers import month_to_start_end_timestamps

from .helpers import (convert_qs, convert_list, verify_product_no,
                      get_timestamps_email, unauthorized, get_usage_class)
from ..models import (TangocloudvmUsage, NectarvmUsage, StorageUsage, HpcUsage, Contact)  # noqa # pylint: disable=unused-import

logger = logging.getLogger(__name__)


# def yearly_usage(request, year):
#     return JsonResponse({'timestamp': year_to_timestamp(year)})

@verify_product_no
def usage_list(request, product_no):
    """List usage of a product in a period defined by start and end"""
    start, end, email = get_timestamps_email(request)
    return _usage_list(email, product_no, start, end)


@verify_product_no
def monthly_usage_list(request, product_no, year, month):
    """List usage of a product in a month of a year"""
    return _usage_list(request.GET['email'], product_no, *month_to_start_end_timestamps(year, month))


@verify_product_no
def usage_summary(request, product_no):
    """List usage summary of a product in a period defined by start and end by orderline"""
    start, end = get_timestamps_email(request, True)
    return _usage_sum(product_no, start, end)


def _usage_list(email, product_no, start, end):
    """List of all records of Price with their native fields"""
    try:
        contact = Contact.get_by_email(email)
    except Contact.DoesNotExist:
        return unauthorized()

    usage_class = get_usage_class(product_no)
    if contact.is_admin:
        orderline_qs = usage_class.create_base_qs(start, end)
    else:
        managed_account_id = contact.get_managed_account_id()
        if managed_account_id:
            orderline_qs = usage_class.create_base_qs(start, end).filter(order__biller_id=managed_account_id)
        else:
            orderline_qs = usage_class.create_base_qs(start, end).filter(order__manager__email=email)

    return convert_list(usage_class.fetch_related(orderline_qs))


def _usage_sum(product_no, start, end):
    """List of all records of Price with their native fields"""
    usage_class = get_usage_class(product_no)
    return convert_qs(usage_class.get(start, end), usage_class.get_default_fields())
