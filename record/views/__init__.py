import logging

import jwt
from django.db.models import F

from ..models import Account, Order
from .helpers import convert_qs, verify_bearer_header, extract_access_token, unauthorized
from oidc.decode import decode
from . import usage, fee, price  # noqa # pylint: disable=unused-import


logger = logging.getLogger(__name__)


@verify_bearer_header
def account(request):
    try:
        access_token = decode(extract_access_token(request))
        # here is demonstration of what are in token
        # email and group could be considered as important
        # infor for authorization
        for k, v in access_token.items():
            logger.debug("%s: %s", k, v)
        return convert_qs(Account.list(), ('dynamics_id', 'name', 'parent'))
    except jwt.PyJWTError:
        return unauthorized()


def contract(request):
    # contract summary
    order_account_manager_qs = Order.objects.select_related('biller', 'manager__account') \
        .annotate(account=F('biller__name'), managerName=F('manager__name'), managerEmail=F('manager__email'), unit=F('manager__account__name'))
    return convert_qs(order_account_manager_qs, ('name', 'account', 'unit', 'managerName', 'managerEmail'))
