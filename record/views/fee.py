# from django.db.models import Sum

from date_helpers import month_to_start_end_timestamps
from ..models import Contact, Fee
from .helpers import (convert_qs, convert_list, verify_product_no,
                      check_required_query_args, require_valid_email, require_auth,
                      unauthorized, get_timestamps_email, get_usage_class)


@check_required_query_args(('email', 'start', 'end'))
@require_auth
@require_valid_email
def fee_list(request):
    """List all records of Fee with their native fields for eRSA only"""
    start, end, email = get_timestamps_email(request)
    contact = Contact.get_by_email(email)

    if contact.is_admin:
        return convert_qs(Fee.objects.filter(start__gte=start, end__lte=end)
                          .order_by('start'), Fee.get_default_fields())

    return unauthorized()


@check_required_query_args(('email', 'start', 'end'))
@require_auth
@require_valid_email
def fee_summary(request):
    start, end, email = get_timestamps_email(request)
    fee_qs = _qs_role_filter(email, Fee.create_summary_qs_base(start, end))
    return convert_list(list(Fee.summary(fee_qs)))


@check_required_query_args(('email', 'start', 'end'))
@verify_product_no
@require_auth
@require_valid_email
def fee_list_by_prod_range(request, product_no):
    start, end, email = get_timestamps_email(request)
    return _fee_by_prod(email, product_no, start, end)


@check_required_query_args(('email', 'start', 'end'))
@verify_product_no
@require_auth
@require_valid_email
def fee_summary_by_prod_range(request, product_no):
    start, end, email = get_timestamps_email(request)
    usage_class = get_usage_class(product_no)
    fee_qs = _qs_role_filter(email, usage_class.create_fee_base_qs(start, end))
    return convert_list(list(Fee.summary(fee_qs)))


@check_required_query_args(('email',))
@verify_product_no
def monthly_fee(request, product_no, year, month):
    return _fee_by_prod(request['email'], product_no, *month_to_start_end_timestamps(year, month))


def _fee_by_prod(email, product_no, start, end):
    """List all records of Fee filtered by product_no with their native fields"""
    # TODO: List all total sum of fee amount in a period grouped by orderline"""
    # e.g. convert_list(list(Fee.objects.filter(start__gte=start, end__lte=end).values('orderline_id').annotate(total_amount=Sum('amount'))))
    usage_class = get_usage_class(product_no)
    fee_qs = _qs_role_filter(email, usage_class.create_fee_base_qs(start, end))
    return convert_qs(fee_qs, Fee.get_default_fields())


def _qs_role_filter(email, qs):
    """Apply role filter to a query set

    :param Queryset usage_base_qs: Queryset created by Usage.create_fee_base_qs
    """
    contact = Contact.get_by_email(email)
    managed_account_id = contact.get_managed_account_id()
    if managed_account_id:
        qs = qs.filter(orderline__order__biller_id=managed_account_id)
    elif not contact.is_admin:
        qs = qs.filter(orderline__order__manager__email=email)

    return qs

# # TODO: how to summary
# def _fee_sum_by_prod(email, product_no, start, end):
#     """List all records of Fee filtered by product_no with their native fields"""
#     try:
#         contact = Contact.get_by_email(email)
#     except Contact.DoesNotExist:
#         return unauthorized()

#     usage_class = get_usage_class(product_no)

#     if contact.is_admin:
#         orderline_qs = usage_class.create_base_qs(start, end)
#     else:
#         managed_account_id = contact.get_managed_account_id()
#         if managed_account_id:
#             orderline_qs = usage_class.create_base_qs(start, end).filter(order__biller_id=managed_account_id)
#         else:
#             orderline_qs = usage_class.create_base_qs(start, end).filter(order__manager__email=email)

#     return convert_list(usage_class.fetch_related(orderline_qs))

#     fee_base_qs = usage_class.create_fee_base_qs(start, end)
#     return convert_list(list(fee_base_qs.values('orderline_id').annotate(total_amount=Sum('amount'))))
