from django.db.models import F

from ..models import Account, Order
from .helpers import convert_qs, require_valid_email, require_auth
from . import usage, fee, price  # noqa # pylint: disable=unused-import

@require_auth
@require_valid_email
def account(request):
    return convert_qs(Account.list(), ('dynamics_id', 'name', 'parent'))

@require_auth
@require_valid_email
def contract(request):
    # contract summary
    order_account_manager_qs = Order.objects.select_related('biller', 'manager__account') \
        .annotate(account=F('biller__name'), managerName=F('manager__name'), managerEmail=F('manager__email'), unit=F('manager__account__name'))
    return convert_qs(order_account_manager_qs, ('name', 'account', 'unit', 'managerName', 'managerEmail'))
