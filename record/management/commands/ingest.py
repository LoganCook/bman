"""
Ingest data from sources and save them into tables
"""

import sys
import logging

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from record.models import Account, Contact, Product, Order, Orderline

from ..utils.command_helper import prepare_command, setup_logger
from ..utils.account_helper import AccountHelper
from ..utils.contact_helper import ContactHelper
from ..utils.contract_helper import Extractor, create_contract_dict

setup_logger(__name__)
logger = logging.getLogger('record.management')


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
                            help='Type of record to be ingested, should match to class name but case insensitive')
        parser.add_argument('--substitutes-json', help='Path to JSON file downloaded from CRM for product substitutions, optional')
        parser.add_argument('--fee', dest='calculate_fee', action='store_true', help='Calculate fee after ingest, default value')
        parser.add_argument('--no-fee', dest='calculate_fee', action='store_false', help='Don not calculate fee after ingest')
        parser.set_defaults(calculate_fee=True)

    # @staticmethod
    # def _get_ingester(normalized_service_name):
    #     # normalized_service_name: prefix of an ingester class which has suffix Ingester
    #     return getattr(ingesters, normalized_service_name + 'Ingester')

    def handle(self, *args, **options):
        # step 1: get an ingest class instance
        try:
            ingester, min_date, max_date, service_config = prepare_command(options)
        except (KeyError, Exception) as err:
            self.stderr.write(err)
            sys.exit(1)

        product_no = service_config['product-no']
        try:
            product = Product.get_by_no(product_no)
        except Exception as err:
            logger.error('Product cannot be found: its number is %s. Detail: %s', product_no, err)
            sys.exit(1)

        msg = 'About to ingest usage data and contracts of %s between %s - %s by %s' \
              % (service_config['product-no'], min_date, max_date, type(ingester).__name__)
        logger.debug(msg)
        self.stdout.write(msg)

        # step 2: make contract info ready for creating Order, Orderline
        # load helper data first
        logger.info('Account helper json=%s', options['account_json'])
        account_helper = AccountHelper(options['account_json'])

        logger.info('Contact helper json=%s', options['contact_json'])
        contact_helper = ContactHelper(options['contact_json'])

        usage_config = ingester.configuration
        crm_config = service_config['CRM']
        try:
            contract_indexer = create_contract_dict(crm_config['url'], crm_config['identifier'])
            usages = ingester.get_data(min_date, max_date)
        except RuntimeError as err:
            logger.error('Cannot get necessary data: %s', str(err))
            sys.exit(1)

        for usage in usages:
            # step 3: use identifiers from CRM and usage to create a super data structure
            if usage[usage_config.orderline_linker] not in contract_indexer:
                logger.warning('Cannot find contract for usage by CRM linking key: %s, value: %s',
                               usage_config.orderline_linker,
                               usage[usage_config.orderline_linker])
                continue
            contract = contract_indexer[usage[usage_config.orderline_linker]]
            # in nectarvm, manager appears in usage data as it has been processed
            # so cannot update using usage, and usage data better not touched
            # there may be some better ways
            augmented_contract = usage.copy()
            augmented_contract.update(contract)

            extractor = Extractor(augmented_contract)
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
                logger.error('Cannot get %s. Check helper JSONs. Current contract: %s', str(err), str(contract))
                continue

            # step 4: create Order
            order_values = extractor.get_order()
            # any account can be a biller
            biller = parent_account if parent_account.name == extractor.get_biller() else child_account
            if biller == None:
                logger.error('No biller for %s', order_values)
                continue
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
                ingester.save(min_date, max_date, orderline, usage, options['calculate_fee'])
            except Exception as err:
                logger.error('Cannot save data into usage table for %s. Error: %s', usage, str(err))
                logger.exception(err)
                break
