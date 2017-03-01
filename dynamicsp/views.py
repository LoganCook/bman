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


# login_conf = settings.BASE_DIR + '/dyncon.json'
# saved_tokens = settings.BASE_DIR + '/saved_tokens.json'
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


product_handler = Product()
products = list_to_dict(product_handler.list_names(), 'name', ('productid', ))
print(products)


def get_product_prop_defs(prod_name):
    """Get nectar sales order details from Dynamics"""
    # name of a selected property is the name of property by removing spaces
    # product_handler = Product()
    selected_properties = None
    if prod_name == 'Nectar Allocation':
        selected_properties = ('OpenstackID', )
    elif prod_name == 'RDS Allocation' or prod_name == 'RDS Backup Allocation':
        selected_properties = ('FileSystemName', 'GrantID')
    return product_handler.get_property_definitions(prod_name, selected_properties)


def get_sold_product(prod_short_name, account_id=None):
    """Get nectar sales order details from Dynamics"""
    # map external names to Dynamics internal names.
    prods = {
        'nectar': 'Nectar Allocation',
        'rds': 'RDS Allocation',
        'rdsbackup': 'RDS Backup Allocation'
    }
    if prod_short_name not in prods:
        return HttpResponseBadRequest("Bad request - unknown product name")

    prod_name = prods[prod_short_name]
    prop_defs = get_product_prop_defs(prod_name)
    manager_role = {'id': settings.PROJECT_ADMIN_ROLE, 'name': 'manager'}
    order_handler = Order()
    if account_id:
        if verify_id(account_id):
            return send_json(order_handler.get_product(products[prod_name]['productid'], account_id=account_id, prod_props=prop_defs, roles=[manager_role]))
        else:
            return send_json([])
    else:
        return send_json(order_handler.get_product(products[prod_name]['productid'], prod_props=prop_defs, roles=[manager_role]))


def get_order_roleid(category_name, role_name):
    """Get Connection role id of an order"""
    # category_name = 'Team'
    # Do not need to run this everytime: settings has three role ids defined so far
    optionsets = Optionset()
    category = optionsets.get_option_from('connectionrole_category', category_name)
    cr = ConnectionRole()
    return cr.get_roleid_of(role_name, category)


def get_for(product_id=None, account_id=None):
    """Get FOR codes of orders

    :return dict: keys are order ids (salesorderid), values are list of strings of 'code: label'
    """
    if product_id and not verify_id(product_id):
        return send_json({})
    if account_id and not verify_id(account_id):
        return send_json({})

    order_handler = Order()
    return send_json(order_handler.get_for_codes(product_id=product_id, account_id=account_id))


def startup(request):
    """return a list of objects can be quired"""
    services = ('organisation', 'nectar', 'rds', 'rdsbackup', 'access')
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
                handler = Account()
                return send_json(handler.get_usernames(kwargs['id']))
            elif kwargs['method'] == 'get_for':
                return get_for(account_id=kwargs['id'], product_id=method_args.get('productid', None))
            else:
                return HttpResponseBadRequest("Bad request - method is not implement for Organisation")
        else:
            return send_json('about an Organisation is not implemented')

    @staticmethod
    def _get_service(account_id, name=None):
        order_handler = Order()

        try:
            if name:
                return get_sold_product(name, account_id)
            else:
                return send_json(order_handler.get_account_products(account_id))
        except LookupError as e:
            logger.error('No record found. Details: %s', str(e))
            return send_json([])


class Nectar(View):
    def get(self, request, *args, **kwargs):
        """Get nectar sales order details from Dynamics"""
        return get_sold_product('nectar')


class RDS(View):
    def get(self, request, *args, **kwargs):
        """Get RDS sales order details from Dynamics"""
        return get_sold_product('rds')


class RDSBackup(View):
    def get(self, request, *args, **kwargs):
        """Get RDS Backup sales order details from Dynamics"""
        return get_sold_product('rdsbackup')


class Access(View):
    def get(self, request, *args, **kwargs):
        """Get eRSA accounts details from Dynamics"""
        contact_handler = Contact()
        return send_json(contact_handler.get_usernames())


class ANZSRCFor(View):
    def get(self, request, *args, **kwargs):
        """Get ANZSRC-FOR codes of Orders"""
        # optional keyword argument productid, ignore any others
        method_args = request.GET.dict()
        order_handler = Order()
        if 'productid' in method_args:
            if verify_id(method_args['productid']):
                return get_for(product_id=method_args['productid'])
            else:
                return send_json([])
        else:
            return send_json(order_handler.get_for_codes())
