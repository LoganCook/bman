from django.db.models import Sum

from ..models import Fee
from .helpers import convert_qs, convert_list, get_usage_class


def fee_all(start, end):
    """List all records of Fee with their native fields"""
    return convert_qs(Fee.objects.filter(start__gte=start, end__lte=end).order_by('start'), Fee.get_default_fields())


def fee_sum(start, end):
    """List all total sum of fee amount in a period grouped by orderline"""
    return convert_list(list(Fee.objects.filter(start__gte=start, end__lte=end).values('orderline_id').annotate(total_amount=Sum('amount'))))


def fee_by_prod(product_no, start, end):
    """List all records of Fee filtered by product number with their native fields"""
    usage_class = get_usage_class(product_no)
    return convert_qs(usage_class.create_fee_base_qs(start, end),
                      Fee.get_default_fields())


def fee_sum_by_prod(product_no, start, end):
    """List all records of Fee filtered by product number with their native fields"""
    usage_class = get_usage_class(product_no)
    fee_base_qs = usage_class.create_fee_base_qs(start, end)
    return convert_list(list(fee_base_qs.values('orderline_id').annotate(total_amount=Sum('amount'))))
