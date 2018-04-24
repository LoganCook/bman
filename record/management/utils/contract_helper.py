import json

from utils import list_to_dict
from . import get_json


def create_contract_dict(url, identifier='OpenstackProjectID', headers=None, timeout=120):
    """Download contract from a url and make it dictionary with identifer as key"""
    # Dynamics needs more time to wake up
    return list_to_dict(get_json(url, headers=headers, timeout=timeout), identifier)


def sort_composed_identifers(crm_linker_name, usage_identifier_names=None):
    """Combine a single-valued crm_linker and a list of usage_identifers

    to build a list of field name to extract values from CRM contract and
    usage data in a determined order to construct a complex identifer string
    """
    # always return a list
    if usage_identifier_names:
        return [crm_linker_name] + sorted(set(usage_identifier_names))
    return [crm_linker_name]


def build_complex_identifer(names, usage_dict):
    """Build a comma delimited string as complex identifier"""
    return ','.join([usage_dict[name] for name in names])


class Extractor(object):
    def __init__(self, content):
        # {
        #   "unitPrice@OData.Community.Display.V1.FormattedValue": "$240.00",
        #   "salesorderdetail2_x002e_transactioncurrencyid@OData.Community.Display.V1.FormattedValue": "Australian Dollar",
        #   "manager": "Some Manager",
        #   "unitPrice": 240,
        #   "salesorderdetail2_x002e_transactioncurrencyid": "744fd97c-18fb-e511-80d8-c4346bc5b718",
        #   "OpenstackProjectID": "vm-2058",
        #   "allocated": 16,
        #   "pricelevelID": "0c407dd9-1b59-e611-80e2-c4346bc58784",
        #   "orderID": "FUSA0167",
        #   "@odata.etag": "W/\"9067518\"",
        #   "managercontactid": "e4bd71c5-5b63-e611-80e3-c4346bc43f98",
        #   "name": "MELFU Virtual Machines",
        #   "manageremail": "some.manager@some.org",
        #   "pricelevelID@OData.Community.Display.V1.FormattedValue": "Members Price List",
        #   "managertitle": "Post Doctoral Researcher - bioinformatician",
        #   "managerunit": "College of Science & Engineering",
        #   "managercontactid@OData.Community.Display.V1.FormattedValue": "Some Manager",
        #   "salesorderid": "f9302faa-7876-e711-8128-70106fa3d971",
        #   "biller": "Flinders University",
        #   "allocated@OData.Community.Display.V1.FormattedValue": "16"
        # }
        self.content = content

    def get_account(self):
        """Return a tuple in the order of biller and managerunit"""
        assert('biller' in self.content and 'managerunit' in self.content)
        return self.content['biller'], self.content['managerunit']

    # FIXME: to be removed
    def get_contact(self):
        return {
            'name': self.content['manager'],
            'email': self.content['manageremail'],
            'accounts': (self.content['biller'], self.content['managerunit'])
        }

    def get_biller(self):
        assert 'biller' in self.content
        return self.content['biller']

    def get_manager(self):
        """Create a dict with only essential information for creating Contact"""
        return {
            'name': self.content['manager'],
            'email': self.content['manageremail'],
            'contactid': self.content['managercontactid'],
            'unit': self.content['managerunit']
        }

    def get_order(self):
        return {
            'dynamics_id': self.content['salesorderid'],
            'name': self.content['name'],
            'no': self.content['orderID'],
            # 'biller': self.content['biller'],
            # 'manager': self.content['manager'],
            # 'manager_email': self.content['manageremail'],
            'price_list': self.content['pricelevelID@OData.Community.Display.V1.FormattedValue']
        }

    def get_orderline(self, id_key):
        # id_key: name of the key for identifier which depends on product
        # id_key does not always set, caller needs to handle the key error
        return {
            'order_id': self.content['salesorderid'],
            'price': self.content['unitPrice'],
            'quantity': self.content['allocated'],
            'identifier': self.content[id_key]
        }


class ProductSubstitute():
    def __init__(self):
        self.substitutes = {}
        # Get identifiers of product with substitutes: can be productid or productnumber even product
        self.main_products = {}
        self.identifiers = ()

    def load_from_file(self, path):
        with open(path, 'r') as jf:
            self._setup(json.load(jf))

    def load_from_web(self, url, headers=None, timeout=120):
        self._setup(get_json(url, headers=headers, timeout=timeout))

    def _setup(self, data_dict):
        self.substitutes = data_dict
        # Get identifiers of product with substitutes: can be productid or productnumber even product
        self.main_products = list_to_dict(self.substitutes, 'productnumber',
                                          ('product', 'productid', 'productnumber', 'producttype', 'productstructure', 'direction'))
        self.identifiers = self.main_products.keys()

    def has_substitute(self, product_no):
        return product_no in self.identifiers

    def get_product_info(self, product_no):
        if self.has_substitute(product_no):
            return self.main_products[product_no]
        return None

    def get_substitutes(self, product_no):
        return [subs for subs in self.substitutes if subs['productnumber'] == product_no]
