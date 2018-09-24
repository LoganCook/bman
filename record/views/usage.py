from date_helpers import month_to_start_end_timestamps

from .helpers import (convert_qs, convert_list, verify_product_no,
                      check_required_query_args, require_valid_email, require_auth,
                      get_timestamps_email, get_usage_class)
from ..models import Contact
from ..models.essentials import MANAGED_ACCOUNT_NOT_FOUND


@check_required_query_args(('email', 'start', 'end'))
@verify_product_no
@require_auth
@require_valid_email
def usage_list(request, product_no):
    """List usage of a product in a period defined by start and end"""
    start, end, email = get_timestamps_email(request)
    return _usage_list(email, product_no, start, end)


@check_required_query_args(('email', ))
@verify_product_no
@require_auth
@require_valid_email
def monthly_usage_list(request, product_no, year, month):
    """List usage of a product in a month of a year"""
    return _usage_list(request.GET['email'], product_no, *month_to_start_end_timestamps(year, month))


@check_required_query_args(('start', 'end', 'email'))
@verify_product_no
@require_auth
@require_valid_email
def usage_simple(request, product_no):
    """List of all records of usage filtered by product_no only with their native fields"""
    start, end, email = get_timestamps_email(request)
    usage_class = get_usage_class(product_no)
    deatil_qs = _qs_role_filter(email, usage_class.get(start, end))
    return convert_qs(deatil_qs, usage_class.get_default_fields())


def _usage_list(email, product_no, start, end):
    """List of all records of usage filtered by product_no with their native fields"""
    usage_class = get_usage_class(product_no)
    orderline_qs = _qs_role_filter(email, usage_class.create_base_qs(start, end))
    return convert_list(usage_class.fetch_related(orderline_qs))


def _qs_role_filter(email, usage_base_qs):
    """Apply role filter to a query set

    :param Queryset usage_base_qs: Queryset created by Usage.create_base_qs
    """
    contact = Contact.get_by_email(email)
    managed_account_name = contact.get_managed_account_name()
    if managed_account_name != MANAGED_ACCOUNT_NOT_FOUND:
        usage_base_qs = usage_base_qs.filter(account=managed_account_name)
    elif not contact.is_admin:
        usage_base_qs = usage_base_qs.filter(managerEmail=email)

    return usage_base_qs
