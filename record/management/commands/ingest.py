"""
Ingest data from sources and save them into tables
"""

import sys
import logging

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from record.models import Account, Contact, Product, Order, Orderline

from .. import LOG_FORMAT, SAN_MS_DATE
# from record.management.importers import Importer
from ..utils import prepare_command
from ..utils.account_helper import AccountHelper
from ..utils.contact_helper import ContactHelper
from ..utils.contract_helper import Extractor, create_contract_dict, ProductSubstitute
from ..ingesters.base import UsageConfiguration
from .. import ingesters

logger = logging.getLogger('record.management')

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=SAN_MS_DATE))
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)


def create_top_account(name, dynamics_id):
    pa, _ = Account.objects.get_or_create(name=name, dynamics_id=dynamics_id)
    return pa


def create_linked_accounts(units):
    """Create parent and child accounts from a tuple of two dict with necessary key-value pairs

    return the account instances
    """
    # units can have one top Account or top and child Accounts
    ca = None
    pa = create_top_account(**units[0])
    if len(units) > 1:
        ca, _ = Account.objects.get_or_create(name=units[1]['name'],
                                              dynamics_id=units[1]['dynamics_id'],
                                              parent_id=pa.pk)
    return pa, ca


def create_contact(name, email, dynamics_id, account):
    contact, _ = Contact.objects.get_or_create(name=name, email=email, dynamics_id=dynamics_id, account=account)
    return contact


def create_order(name, no, dynamics_id, biller, manager, price_list):
    order, _ = Order.objects.get_or_create(name=name, no=no, dynamics_id=dynamics_id, biller=biller, manager=manager, price_list=price_list)
    return order


def get_order(name, no, dynamics_id, price_list):
    return Order.objects.get(name=name, no=no, dynamics_id=dynamics_id, price_list=price_list)


def create_orderline(order, product, info):
    line, _ = Orderline.objects.get_or_create(order=order,
                                              product=product,
                                              #   dynamics_id=info['dynamics_id'],  # this is not used as contract does not have it yet
                                              quantity=info['quantity'],
                                              price=info['price'],
                                              identifier=info['identifier'])
    return line


def get_orderline(order, product, info):
    return Orderline.objects.get(order=order,
                                 product=product,
                                 #   dynamics_id=info['dynamics_id'],  # this is not used as contract does not have it yet
                                 quantity=info['quantity'],
                                 price=info['price'],
                                 identifier=info['identifier'])


class Command(BaseCommand):
    # identifier in CRM is parent identifier, temporary
    # To create Orderline, this possibly needs to be more specific: for example, nectar, it needs to
    # convert from tenant (project, OpenstackProjectID) to server_id
    help = 'Ingest data from a BMAN and usage endpoints and create Order, Orderline and usage data at the same time'

    def add_arguments(self, parser):
        required_kargs = parser.add_argument_group('required named arguments')
        required_kargs.add_argument('-s', '--start', help='Start date (%%Y%%m%%d) of the interval', required=True)
        required_kargs.add_argument('-e', '--end', help='End date "(%%Y%%m%%d)" of the interval', required=True)
        required_kargs.add_argument('--account-json', help='Path to JSON file downloaded from CRM for accounts', required=True)
        required_kargs.add_argument('--contact-json', help='Path to JSON file downloaded from CRM for contacts', required=True)

        parser.add_argument('-c', '--conf',
                            default='config.json',
                            help='Path to configuration JSON file. Default = config.json')
        parser.add_argument('-t', '--type',
                            default='tangocloudvm',
                            choices=['tangocloudvm', 'nectarvm', 'xfs', 'hcp', 'hnasvv', 'hnasfs', 'hpc'],
                            help='Type of ingestion, should match to class name but case insensitive')
        parser.add_argument('--substitutes-json', help='Path to JSON file downloaded from CRM for product substitutions, optional')

    @staticmethod
    def _get_ingester(normalized_service_name):
        # normalized_service_name: prefix of an ingester class which has suffix Ingester
        return getattr(ingesters, normalized_service_name + 'Ingester')

    def handle(self, *args, **options):
        try:
            service, min_date, max_date, service_config = prepare_command(options)
        except Exception as err:
            self.stderr.write(err)
            sys.exit(1)

        product_no = service_config['product-no']
        try:
            product = Product.get_by_no(product_no)
        except Exception as err:
            logger.error('Product cannot be found: its number is %s. Detail: %s', product_no, err)
            sys.exit(1)

        # load helper data first
        account_helper = AccountHelper(options['account_json'])
        contact_helper = ContactHelper(options['contact_json'])
        # product substitutes
        if options['substitutes_json']:
            substitutes = ProductSubstitute()
            substitutes.load_from_file(options['substitutes_json'])
        else:
            substitutes = None

        # Make contracts availabe for later use
        crm_config = service_config['CRM']
        product_no = service_config['product-no']
        usage_config = UsageConfiguration(product_no, service_config['USAGE'])

        # step 1: get usage data
        try:
            ingester_class = self._get_ingester(service)
        except KeyError:
            self.stderr.write('Cannot load ingester class by its prefix %s' % service)
            sys.exit(1)

        ingester = ingester_class(usage_config, substitutes)

        msg = 'About to ingest usage data and contracts between %s - %s for service %s (%s) into the database' % (min_date, max_date, service, product_no)
        logger.debug(msg)
        self.stdout.write(msg)

        # step 2: make contract info ready for creating Order, Orderline
        contract_indexer = create_contract_dict(crm_config['url'], crm_config['identifier'])
        usages = ingester.get_data(min_date, max_date)
        for usage in usages:
            # step 3: use identifiers from CRM and usage to create a super data structure
            if usage[usage_config.orderline_linker] not in contract_indexer:
                logger.warning('Cannot find contract for usage by CRM linking key: %s, value: %s',
                               usage_config.orderline_linker,
                               usage[usage_config.orderline_linker])
                continue
            contract = contract_indexer[usage[usage_config.orderline_linker]]
            contract.update(usage)

            extractor = Extractor(contract)
            try:
                manager_info = extractor.get_manager()
                contact = contact_helper.get(manager_info['email'])
                # can be one or two in return
                units = account_helper.get_contact_accounts(contact['unit_dynamics_id'])
                # create accounts from manager's information
                parent_account, child_account = create_linked_accounts(units)
                # create contact for manager
                if child_account:
                    manager = create_contact(manager_info['name'], manager_info['email'], manager_info['contactid'], child_account)
                else:
                    manager = create_contact(manager_info['name'], manager_info['email'], manager_info['contactid'], parent_account)
            except (KeyError, NameError) as err:
                logger.error('%s, %s', str(err), str(contract))
                continue

            # step 4: create Order
            order_values = extractor.get_order()
            # any account can be a biller
            biller = parent_account if parent_account.name == extractor.get_biller() else child_account
            assert biller != None
            assert manager != None
            order_values['biller'] = biller
            order_values['manager'] = manager
            try:
                order = create_order(**order_values)
            except IntegrityError as err:
                logger.warning('Order has been created before: %s', order_values)
                order = get_order(order_values['name'], order_values['no'], order_values['dynamics_id'], order_values['price_list'])
            except Exception as err:
                logger.error('Cannot create order for %s', order_values)
                logger.error(str(err))
                continue

            # step 5: create Orderline
            try:
                orderline_info = extractor.get_orderline(usage_config.orderline_linker)
                # build a record.orderline identifier by combining
                # crm-linker and aggregators from usage data
                orderline_info['identifier'] = usage_config.create_orderline_identifer(usage)
                orderline = create_orderline(order, product, orderline_info)
            except KeyError as err:
                logger.warning('Incomplete orderline data - missing key: %s in %s, %s',
                               err, contract['orderID'], contract['salesorderid'])
                continue
            except IntegrityError as err:
                # May move this into create_orderline to make it create_get
                logger.warning('Orderline has been created before: order: %s, product: %s, extra: %s',
                               order, product, orderline_info)
                orderline = get_orderline(orderline, product, orderline_info)

            # step 6: create usage, fee
            try:
                ingester.save(min_date, max_date, orderline, usage, False)
            except Exception as err:
                logger.error('Cannot save data into usage table for %s. Error: %s', usage, str(err))
                logger.exception(err)
                break
