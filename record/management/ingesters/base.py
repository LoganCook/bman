import logging
from django.core.exceptions import ObjectDoesNotExist

from utils import dict_to_object
from ...models import Orderline, Product, Fee
from ..utils.contract_helper import sort_composed_identifers, build_complex_identifer
from ..utils import get_json


logger = logging.getLogger(__name__)


def repacke(conf, source):
    """Create a new dict using a mapping conf from a source dict

    key in conf: key in source dict
    value in conf: key in the new dict
    """
    result = {}
    for (k, v) in conf.items():
        result[v] = source[k]
    return result


# {
#   "Nectarvm": {
#     "product-no": "325620",
#     "CRM": {
#       "url": "http://144.6.236.232/bman/api/v2/contract/nectarcloudvm/",
#       "identifier": "OpenstackProjectID"
#     },
#     "USAGE": {
#       "original-data": {
#         "url": "https://reporting.ersa.edu.au/usage/nova"
#       },
#       "fields": {
#         "span": "span"
#       },
#       "orderline": {
#         "crm-linker": "tenant",
#         "aggregators":[
#            "list",
#            "of usage fields which will be used to create a composed identifier in orderline",
#            "one example is queue in tizard"],
#         "extra" : {
#           "hypervisor": "hypervisor",
#           "server": "server",
#           "vcpus": "vcpus",
#           "ram": "ram",
#           "disk": "disk",
#           "ephemeral": "ephemeral",
#           "name": "flavor"
#         }
#       },
#       "fee-field": "vcpus",
#       "flavor-json-path": "record/flavors.json"
#     }
#   }
# }
class UsageConfiguration:
    """A configuration for ingesting information from usage data

    It must have:
    1. original-data
        1. url for getting data
        2. identifier for linking usage data to an orderline with help of product-no
        3. headers for getting data
    2. fields: field map for mapping from usage data fields to table fields
    3. orderline for mapping usage data fields to orderline configuration

    It can also have:
    fee-field or composition for mapping composing product numbers to usage data fields for calculating fee
    """
    def __init__(self, prod_no, conf):
        # a configuration
        self.configuration = self._validate(conf)
        self.product_no = prod_no

    def _validate(self, conf):
        """Validate configuration"""
        if 'original-data' not in conf:
            raise KeyError('Configuration error: missing original-data.')
        if 'url' not in conf['original-data']:
            raise KeyError('Configuration error: missing url for original-data.')
        if 'orderline' not in conf:
            raise KeyError('Configuration error: missing orderline.')
        if 'crm-linker' not in conf['orderline']:
            raise KeyError('Configuration error: missing crm-linker for orderline.')
        # fee-field and composition cannot co-exist
        if 'fee-field' in conf and 'composition' in conf:
            raise KeyError('Configuration error: fee-field and composition cannot be set at the same time.')
        if 'fee-field' not in conf and 'composition' not in conf:
            raise KeyError('Configuration error: Either fee-field or composition has been defined.')
        return conf

    @property
    def url(self):
        """url to get data from"""
        return self.configuration['original-data']['url']

    @property
    def headers(self):
        """Optional property if data endpoints requires"""
        if 'headers' in self.configuration['original-data']:
            return self.configuration['original-data']['headers']
        return None

    @property
    def fields(self):
        return self.configuration['fields']

    # TODO: merge this with compostion to simplify fee calculation
    # fee-fields = { 'product_no1': 'field1', 'product_no2': 'field2'}
    # in _validate, confirm self.product_no in fee-fields
    @property
    def fee_field(self):
        if 'fee-field' in self.configuration and 'composition' not in self.configuration:
            return self.configuration['fee-field']
        raise KeyError('fee-field is either not defined or has composition at the same time.')

    @property
    def orderline_linker(self):
        """Key name used to match the identifier of CRM contract"""
        # Use this only to find a matching CRM contract record
        # Do not use this to create identifier in Orderline table
        return self.configuration['orderline']['crm-linker']

    @property
    def has_aggregators(self):
        return 'aggregators' in self.configuration['orderline']

    @property
    def orderline_aggregators(self):
        assert isinstance(self.configuration['orderline']['aggregators'], list)
        return self.configuration['orderline']['aggregators']

    @property
    def orderline_identifier_list(self):
        """Get a list of field name for extracting values to build a compose identifier in Orderline"""
        # Use this only to create identifier in Orderline
        aggregators = self.orderline_aggregators if self.has_aggregators else None
        return sort_composed_identifers(self.orderline_linker, aggregators)

    @property
    def orderline_configuration_map(self):
        return self.configuration['orderline']['extra']

    @property
    def is_for_composed_product(self):
        # 'composition' and 'fee-field' are exclusive
        return 'composition' in self.configuration and 'fee-field' not in self.configuration

    @property
    def composition_map(self):
        """A map from product numbers to usage data fields in usage table for calculating fee"""
        assert 'fee-field' not in self.configuration
        return self.configuration['composition']

    def create_orderline_identifer(self, usage):
        """Create a string for creating identifier in orderline table

        :param dict usage: usage dict object
        """
        return build_complex_identifer(self.orderline_identifier_list, usage)


class UsageIngester:
    def __init__(self, usage_conf, substitutes=None):
        """
        :param UsageConfiguration usage_conf: ingestion configuration
        :param ProductSubstitute substitutes: helper of checking complex product.
        """
        self.configuration = usage_conf
        # TODO: how to cache properly? current one will mess up with orders with different price lists
        self.single_price = -1
        self.composed_prices = {}
        product_no = self.configuration.product_no
        main_product = Product.get_by_no(product_no)

        # billing_items: {
        #    product_number1: {"type": "some type", "field": "usage field name"}
        #    product_number2: {"type": "some type", "field": "usage field name"}
        #    product_number3: {"type": "Flat Fees"}
        # }
        # Prepare a map of field to product (number)
        # Flat fee as a substitute? not appear in composition, field will be empty
        if substitutes and substitutes.has_substitute(product_no):
            # Only eRSA reserved relationtype Accessory can be used in such situation
            accessories = [sub for sub in substitutes.get_substitutes(product_no) if sub['salesrelationshiptype'] == 'Accessory']
            self.billing_items = {}
            for accessory in accessories:
                if accessory['substitutedproducttype'] == 'Flat Fees':
                    self.billing_items[accessory['substitutedproductnumber']] = {'type': accessory['substitutedproducttype']}
                else:
                    self.billing_items[accessory['substitutedproductnumber']] = \
                        {'type': accessory['substitutedproducttype'],
                         'field': self.configuration.composition_map[accessory['substitutedproductnumber']]}

            if main_product.type != 'Miscellaneous Charges':
                # self.configuration.fee_field is optional
                # currently fee_field and composition_map are exclusive - 20180627
                self.billing_items[main_product.no] = {'type': main_product.type, 'field': self.configuration.fee_field}
        else:
            self.billing_items = {product_no: {'type': main_product.type, 'field': self.configuration.fee_field}}

    @staticmethod
    def _get_price_of(product_no, list_name, start, end):
        """Convert a yearly price from CRM to a price suits to the period"""
        # converted through day: 3600 / 24 / 365 = 31536000
        finder = Product.get_by_no(product_no).get_price_finder()
        yearly = finder.get_price(list_name, start, end)
        return yearly * (end - start) / 31536000

    def _get_price(self, list_name, start, end):
        # FIXME: does not respect list_name in cache
        if self.single_price < 0:
            self.single_price = self._get_price_of(self.configuration.product_no, list_name, start, end)
        return self.single_price

    # def _get_prices(self, list_name, start, end):
    #     # TODO: not used, to be removed?
    #     assert self.is_complex_product
    #     if not self.composed_prices or list_name not in self.composed_prices:

    #         for (prod_no, field) in self.configuration.composition_map.items():
    #             self.composed_prices[field] = self._get_price_of(prod_no, list_name, start, end)
    #     return self.composed_prices

    def _build_orderline_identifer(self, usage):
        """Extract field values by a list of names and concat to a string by comma"""
        return ','.join([str(usage[field]) for field in self.configuration.orderline_identifier_list])

    def _get_orderline(self, usage):
        try:
            identifier = usage[self._build_orderline_identifer(usage)]
            return Orderline.get_by_identifier(identifier, self.configuration.product_no)
        except (ObjectDoesNotExist, IndexError):
            raise ObjectDoesNotExist('No order found for instance with id=%s, product number=%s' % (identifier, self.configuration.product_no))

    def get_usage_class(self):
        """Get the usage class this ingester manages"""
        raise NotImplementedError

    def get_data(self, start, end):
        # tangovm - vms only has monthly data, in database, there is only the start of month, so we cannot do partial monthly report
        args = {'start': start, 'end': end}
        return get_json(self.configuration.url, args, self.configuration.headers)

    # def get_product_substitutes(self):
    #     return self.product_substitutes.get_substitutes(self.configuration.product_no)

    def get_fee_field_value(self, usage, field_name):
        """Extract a field from an object - for derived classes to override

        For example, for some fields, converting units for calculation.
        """
        return getattr(usage, field_name)

    def calculate_fee(self, usage, start, end):
        fee = 0
        for product_no in self.billing_items:
            # Product of Miscellaneous Charges is pseudo should not be a part of calculation
            assert self.billing_items[product_no]['type'] != 'Miscellaneous Charges'
            if self.billing_items[product_no]['type'] == 'Flat Fees':
                fee = fee + self._get_price_of(product_no, usage.orderline.order.price_list, start, end)
            else:
                fee = fee + self._get_price_of(product_no, usage.orderline.order.price_list, start, end) \
                    * self.get_fee_field_value(usage, self.billing_items[product_no]['field'])
        return fee

    def save_config(self, orderline, usage):
        raise NotImplementedError

    def prepare_usage(self, orderline, start, end, usage):
        """Prepare usage data for save method"""
        data = {
            'orderline_id': orderline.id,
            'start': start,
            'end': end
        }
        for ori, target in self.configuration.fields.items():
            data[target] = usage[ori]
        return data

    def save_usage(self, orderline, start, end, usage):
        usage_class = self.get_usage_class()
        data = self.prepare_usage(orderline, start, end, usage)
        try:
            usage_class.objects.get_or_create(**data)
        except Exception as err:
            logger.error('Failed to save %s usage: orderlie id=%s between %d - %d, detail: %s', usage_class.__name__, orderline.id, start, end, err)
        return data

    def get_usage(self, start, end):
        raise NotImplementedError

    def save(self, start, end, orderline, usage, calculate_fee=False):
        """Save a usage entry, calculate fee when is needed"""
        # Used when orderline can only be created use the help from usage data
        # nectar is typical
        try:
            self.save_config(orderline, usage)
            saved_data = self.save_usage(orderline, start, end, usage)
            if calculate_fee:
                fake_usage_instance = dict_to_object(saved_data)
                fake_usage_instance.orderline = orderline
                fee = self.calculate_fee(fake_usage_instance, start, end)
                Fee.objects.get_or_create(orderline=orderline, start=start, end=end, amount=fee)
            logger.debug('Ingested %s', usage)
        except ObjectDoesNotExist as err:
            logger.warning('%s: %s', str(err), str(usage))
        except Exception as err:
            logger.error('%s %s %s', err, usage, orderline)
            logger.exception(err)

    def calculate_fees(self, start, end):
        """Calculate fees for a period from a usage table"""
        for usage in self.get_usage(start, end):
            try:
                # not optimized
                fee = self.calculate_fee(usage, start, end)
                Fee.objects.get_or_create(orderline_id=usage.orderline_id, start=start, end=end, amount=fee)
            except Exception as err:
                logger.error(str(err))
