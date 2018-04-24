from django.http import JsonResponse
from django.db.models import F, Prefetch, Sum, Avg

from date_helpers import month_to_start_end_timestamps
from ..models import Account, Manager, Order, Orderline, Fee, Tangocloudvm, TangocloudvmUsage
from .helpers import convert_qs, cors_response, verify_product_no, _get_timestamps_email
from .fee import fee_all, fee_sum, fee_by_prod, fee_sum_by_prod
from . import usage, price


def account(request):
    return convert_qs(Account.list(), ('dynamics_id', 'name', 'parent'))


def contract(request):
    # contract summary
    order_account_manager_qs = Order.objects.select_related('biller', 'manager__account') \
        .annotate(account=F('biller__name'), managerName=F('manager__name'), managerEmail=F('manager__email'), unit=F('manager__account__name'))
    return convert_qs(order_account_manager_qs, ('name', 'account', 'unit', 'managerName', 'managerEmail'))


def fee_list(request):
    start, end = _get_timestamps_email(request, True)
    return fee_all(start, end)


def fee_summary(request):
    start, end = _get_timestamps_email(request, True)
    return fee_sum(start, end)


@verify_product_no
def fee_by_prod_range(request, product_no):
    start, end = _get_timestamps_email(request, True)
    return fee_by_prod(product_no, start, end)


@verify_product_no
def fee_summary_by_prod_range(request, product_no):
    start, end = _get_timestamps_email(request, True)
    return fee_sum_by_prod(product_no, start, end)


@verify_product_no
def monthly_fee(request, product_no, year, month):
    return fee_by_prod(product_no, *month_to_start_end_timestamps(year, month))


def package_tango_data(orderlines_qs):
    def extract_config(qs):
        return qs.values(*Tangocloudvm.get_default_fields())[0]

    def sum_fee(qs):
        return qs.values('orderline_id').annotate(total_fee=Sum('amount'))[0]

    def sum_usage(qs):
        # only span can be summed, others have to be averaged
        return qs.values('orderline_id').annotate(total_span=Sum('span'), avg_storage=Avg('storage'), avg_uptime=Avg('uptime_percent'))[0]

    def extract_value(instance, values):
        result = {}
        for value in values:
            result[value] = getattr(instance, value)
        return result

    main_fields = 'name', 'account', 'unit', 'manager', 'email', 'price', 'identifier'
    results = []
    for ol in orderlines_qs:
        result = extract_value(ol, main_fields)
        temp = sum_fee(ol.fee_set)
        result.update(temp)
        temp = sum_usage(ol.tangocloudvmusage_set)
        result.update(temp)
        result.update(extract_config(ol.tangocloudvm_set))
        results.append(result)
    return cors_response(JsonResponse(results, safe=False))


def create_tango_base_qs(start, end):
    # This is a transition function for frontend until it has been fully rewritten
    # http://127.0.0.1:8000/vms/instance/?start=1519824600&end=1522502999
    # It needs fee and usage order
    # Currently only for admin, no filtering of biller or manager
    # date filter is done on fee and usage through orderlines
    fee_qs = Fee.objects.filter(start__gte=start, end__lte=end)
    usage_qs = TangocloudvmUsage.objects.filter(start__gte=start, end__lte=end)
    orderline_id_qs = fee_qs.distinct().values_list('orderline_id', flat=True)

    prefetch_fee = Prefetch('fee_set', queryset=fee_qs)
    prefetch_usage = Prefetch('tangocloudvmusage_set', queryset=usage_qs)

    # fee filtered as the base
    return Orderline.objects.filter(pk__in=orderline_id_qs).select_related('order__biller', 'order__manager__account').prefetch_related('tangocloudvm_set', prefetch_usage, prefetch_fee) \
        .annotate(name=F('order__name'), account=F('order__biller__name'), unit=F('order__manager__account__name'), managerName=F('order__manager__name'), managerEmail=F('order__manager__email'))


# Security checking here can be easily bypassed
def tango_temp_admin(request):
    # This url currently is not checked who can access.
    start, end = _get_timestamps_email(request, True)
    return package_tango_data(create_tango_base_qs(start, end))


def tango_temp(request):
    start, end, email = _get_timestamps_email(request)
    # account manager query
    # FIXME: this quick way may not the best solution: Use Contact as the starting point instead
    manager_account_id = Manager.get_managed_account_id(email)
    if manager_account_id is None:
        return _tango_temp_owner(start, end, email)
    orderlines_qs = create_tango_base_qs(start, end).filter(order__biller_id=manager_account_id)
    return package_tango_data(orderlines_qs)


def _tango_temp_owner(start, end, email):
    # Owner query
    orderlines_qs = create_tango_base_qs(start, end).filter(order__manager__email=email)
    return package_tango_data(orderlines_qs)
