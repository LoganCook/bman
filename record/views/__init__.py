from django.db.models import F

from ..models import Account, Order
from .helpers import convert_qs, verify_bearer_header
from oidc.decode import decode
from . import usage, fee, price  # noqa # pylint: disable=unused-import


@verify_bearer_header
def account(request):
    return convert_qs(Account.list(), ('dynamics_id', 'name', 'parent'))


def contract(request):
    # contract summary
    order_account_manager_qs = Order.objects.select_related('biller', 'manager__account') \
        .annotate(account=F('biller__name'), managerName=F('manager__name'), managerEmail=F('manager__email'), unit=F('manager__account__name'))
    return convert_qs(order_account_manager_qs, ('name', 'account', 'unit', 'managerName', 'managerEmail'))
