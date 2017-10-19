# python manage.py runserver --sett runner.dynamicsp
import uuid
import logging

from django.conf import settings
from django.views.generic import View
from django.http import HttpResponseBadRequest, JsonResponse

from edynam import connect
from edynam.models import Account, Contact, Order, Product, Optionset, ConnectionRole

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s %(asctime)s %(filename)s %(module)s.%(funcName)s +%(lineno)d: %(message)s')

logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

login_conf = settings.DYNAMICS_CONF
saved_tokens = settings.TOKENS_JSON
connect(login_conf, saved_tokens)


def send_json(py_data):
    response = JsonResponse(py_data, safe=False)
    response["Access-Control-Allow-Origin"] = "*"
    return response


def list_to_dict(list_of_dict, key_name, value_names=None):
    dic = {}
    if value_names:
        for item in list_of_dict:
            dic[item[key_name]] = {}
            for vk in value_names:
                dic[item[key_name]][vk] = item[vk]
    else:
        for item in list_of_dict:
            del item[key_name]
            dic[item[key_name]] = item
    return dic


def verify_id(dynamics_id):
    """Verify if a string claimed as a Dynamics ID is an UUID"""
    # This will avoid travel to Dynamics server if it is not an UUID
    is_valid = True
    try:
        uuid.UUID(dynamics_id)
    except ValueError:
        is_valid = False
    return is_valid


class ProductInfo(object):
    def __init__(self):
        self.product_handler = Product()
        self.products = list_to_dict(self.product_handler.list_names(), 'name', ('productid', ))
        self._normalise_names()

    def _normalise_names(self):
        """Create a map which holds normalised internal product names which are used in urls"""
        self.normalised_names = {}
        for long_name in self.products:
            self.normalised_names[long_name.lower().replace('allocation', '').replace(' ', '')] = long_name

    def get_internal_name(self, short_name):
        if short_name not in self.normalised_names:
            raise LookupError("Unknown product name")
        return self.normalised_names[short_name]

    def get_id(self, name):
        # Not supposedly be used directly in view functions
        # It should be called after get_internal_name
        return self.products[name]['productid']

    def get_product_prop_defs(self, name):
        """Get Product properties needed for quering Orders"""
        # name of a selected property is the name of property by removing spaces
        selected_properties = None
        if name == 'Nectar Allocation':
            selected_properties = ('OpenstackID', )
        elif name == 'RDS Allocation' or name == 'RDS Backup Allocation':
            selected_properties = ('FileSystemName', 'GrantID')
        return self.product_handler.get_property_definitions(name, selected_properties)


# Object facilitates getting product names and properties
products = ProductInfo()
# These are not real products at all but with different meta data
REPORT_PRODUCTS = ('ands_report', 'rds_report')


def get_sold_product(prod_short_name, account_id=None):
    """Get sales order details of a product from Dynamics"""
    if prod_short_name in REPORT_PRODUCTS and account_id:
        if prod_short_name == 'ands_report':
            meta = _get_ands_report_meta(account_id)
        elif prod_short_name == 'rds_report':
            meta = _get_ands_report_meta(account_id)
        return meta

    try:
        prod_name = products.get_internal_name(prod_short_name)
    except LookupError:
        return HttpResponseBadRequest("Bad request - unknown product name")

    prop_defs = products.get_product_prop_defs(prod_name)
    # CRM project admin role is manager except in ANDS report (admin) at the frontend
    # CRM project leader role is leader at the frontend for ANDS (not widely used)
    if prod_short_name in ('ersaaccount', 'tangocompute'):
        manager_role = {'id': settings.PROJECT_ADMIN_ROLE, 'name': 'manager', 'extra': [('new_username', 'username')]}
    else:
        manager_role = {'id': settings.PROJECT_ADMIN_ROLE, 'name': 'manager'}
    order_handler = Order()
    if account_id:
        if verify_id(account_id):
            return order_handler.get_product(products.get_id(prod_name), account_id=account_id, prod_props=prop_defs, roles=[manager_role])
        else:
            return []
    else:
        return order_handler.get_product(products.get_id(prod_name), prod_props=prop_defs, roles=[manager_role])


def _get_ands_report_meta(account_id):
    """Get meta data from Dynamics about RDS and RDS Backup allocations
    for ANDS NodeConnect report"""

    def get_report_product(prod_short_name, account_id):
        """Get sales order details from Dynamics"""
        prod_name = products.get_internal_name(prod_short_name)
        prop_defs = products.get_product_prop_defs(prod_name)
        roles = ({'id': settings.PROJECT_ADMIN_ROLE, 'name': 'admin'}, {'id': settings.PROJECT_LEADER_ROLE, 'name': 'leader'})
        extra = ({'name': 'description'}, )
        order_handler = Order()
        return order_handler.get_product(products.get_id(prod_name), account_id=account_id, prod_props=prop_defs, roles=roles, order_extra=extra)

    rds = get_report_product('rds', account_id)
    rds.extend(get_report_product('rdsbackup', account_id))
    return rds


def get_order_roleid(category_name, role_name):
    """Get Connection role id of an order"""
    # category_name = 'Team'
    # Do not need to run this everytime: settings has three role ids defined so far
    optionsets = Optionset()
    category = optionsets.get_option_from('connectionrole_category', category_name)
    cr = ConnectionRole()
    return cr.get_roleid_of(role_name, category)


def get_for(product=None, account_id=None):
    """Get FOR codes of orders

    :param str product: short name of a Product, default None
    :param str account_id: Account's UUID, default None
    :return dict: keys are order ids (salesorderid), values are list of strings of 'code: label'
    :raise Bad request exception when product cannot be mapped to an internal name
    """
    if account_id and not verify_id(account_id):
        return send_json({})

    if product:
        try:
            prod_name = products.get_internal_name(product)
        except LookupError:
            return HttpResponseBadRequest("Bad request - unknown product name")
        else:
            product_id = products.get_id(prod_name)
    else:
        product_id = None

    order_handler = Order()
    return send_json(order_handler.get_for_codes(product_id=product_id, account_id=account_id))


def startup(request):
    """return a list of objects can be quired"""
    services = ('organisation', 'nectar', 'rds', 'rdsbackup', 'access', 'ersaaccount', 'tangocompute')
    return send_json(services)


class Organisations(View):
    """Queries of all organisations"""
    def get(self, request, *args, **kwargs):
        kwargs.update(request.GET.dict())
        if 'method' in kwargs and kwargs['method'] in ('get_tops', ):
            return self._get_tops()
        else:
            return self._list()

    @staticmethod
    def _get_tops():
        handler = Account()
        return send_json(handler.get_top())

    @staticmethod
    def _list():
        return send_json('List of all organisations (accounts) is not implemented')


class Organisation(View):
    """Queries of an organisation"""
    def get(self, request, *args, **kwargs):
        # request url is in this format with all parts optional:
        # /(id)?/(method)?/?arg1=one&arg2=two
        # instance methods - always have id, can have method and its args
        #    without method, return object itself
        if 'id' not in kwargs:
            return HttpResponseBadRequest("Bad request - missing id")

        if not verify_id(kwargs['id']):
            return send_json([])

        if 'method' in kwargs:
            method_args = request.GET.dict()
            if kwargs['method'] == 'get_service':
                return self._get_service(kwargs['id'], **method_args)
            elif kwargs['method'] == 'get_access':
                # TODO: Do we still need usernames at organisational level?
                handler = Account()
                return send_json(handler.get_usernames(kwargs['id']))
            elif kwargs['method'] == 'get_for':
                return get_for(account_id=kwargs['id'], product=method_args.get('product', None))
            else:
                return HttpResponseBadRequest("Bad request - method is not implement for Organisation")
        else:
            return send_json('About an Organisation is not implemented')

    @staticmethod
    def _get_service(account_id, name=None):
        # Better named as _get_service_info?
        order_handler = Order()

        try:
            if name:
                return send_json(get_sold_product(name, account_id))
            else:
                return send_json(order_handler.get_account_products(account_id))
        except LookupError as e:
            logger.error('No record found. Details: %s', str(e))
            return send_json([])


class Nectar(View):
    def get(self, request, *args, **kwargs):
        """Get nectar sales order details from Dynamics"""
        return send_json(get_sold_product('nectar'))


class RDS(View):
    def get(self, request, *args, **kwargs):
        """Get RDS sales order details from Dynamics"""
        return send_json(get_sold_product('rds'))


class RDSBackup(View):
    def get(self, request, *args, **kwargs):
        """Get RDS Backup sales order details from Dynamics"""
        return send_json(get_sold_product('rdsbackup'))


class Access(View):
    def get(self, request, *args, **kwargs):
        """Get eRSA accounts usernames from Dynamics"""
        contact_handler = Contact()
        return send_json(contact_handler.get_usernames())


class ERSAAccount(View):
    def get(self, request, *args, **kwargs):
        """Get Orders of eRSA Account - HPC"""
        return send_json(get_sold_product('ersaaccount'))

class TangoCompute(View):
    def get(self, request, *args, **kwargs):
        """Get Orders of TANGO Compute -HPC"""
        return send_json(get_sold_product('tangocompute'))

class ANZSRCFor(View):
    def get(self, request, *args, **kwargs):
        """Get ANZSRC-FOR codes of Orders"""
        # optional keyword argument product is product short name, ignore any others
        method_args = request.GET.dict()
        return get_for(product=method_args.get('product', None))


class RDSReport(View):
    """Get meta data from Dynamics about RDS and RDS Backup allocations
    for RDS Storage node collection report"""
    # This report only needs order id, order title, allocated size
    def get(self, request, *args, **kwargs):
        def get_report_product(prod_short_name):
            """Get sales order details from Dynamics"""
            prod_name = products.get_internal_name(prod_short_name)
            prop_defs = products.get_product_prop_defs(prod_name)
            order_handler = Order()
            return order_handler.get_product(products.get_id(prod_name), prod_props=prop_defs)

        rds = get_report_product('rds')
        rds.extend(get_report_product('rdsbackup'))
        return send_json(rds)
