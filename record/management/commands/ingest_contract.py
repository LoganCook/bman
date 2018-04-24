"""
Ingest contract from an endpoint
"""

import sys
import logging

from django.core.management.base import BaseCommand

from .. import LOG_FORMAT, SAN_MS_DATE
# from record.management.importers import Importer
from ..utils import read_conf, get_json, Extractor
from ..utils.account_helper import AccountHelper
from ..utils.contact_helper import ContactHelper
from record.models import Account, Contact, Product, Order, Orderline

logger = logging.getLogger('record.management')

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=SAN_MS_DATE))
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)


def create_linked_accounts(linked_account_names, helper):
    """Create parent and child accounts from a tuple of two dict with necessary key-value pairs

    return the account instances
    """
    parent, child = helper.get_accounts(linked_account_names)
    pa, _ = Account.objects.get_or_create(**parent)
    ca, _ = Account.objects.get_or_create(name=child['name'],
                                          dynamics_id=child['dynamics_id'],
                                          parent_id=pa.pk)
    return pa, ca


def create_contact(name, email, dynamics_id, account):
    contact, _ = Contact.objects.get_or_create(name=name, email=email, dynamics_id=dynamics_id, account=account)
    return contact


def create_order(name, no, dynamics_id, biller, manager, price_list):
    order, _ = Order.objects.get_or_create(name=name, no=no, dynamics_id=dynamics_id, biller=biller, manager=manager, price_list=price_list)
    return order


def create_orderline(order, product, info):
    line, _ = Orderline.objects.get_or_create(order=order,
                                              product=product,
                                              #   dynamics_id=info['dynamics_id'],  # this is not used as contract does not have it yet
                                              quantity=info['quantity'],
                                              price=info['price'],
                                              identifier=info['identifier'])
    return line


class Command(BaseCommand):
    help = 'Ingest data from a BMAN and usage endpoints'

    def add_arguments(self, parser):
        parser.add_argument('-t', '--type',
                            default='tangocloudvm',
                            choices=['tangocloudvm', 'nectarvm'],
                            help='Type of ingestion')

        parser.add_argument('-c', '--conf',
                            default='config.json',
                            help='Path to configuration JSON file. Default = config.json')

    def handle(self, *args, **options):
        service = options['type'].capitalize()
        config = read_conf(options['conf'])
        logger.info("Config file path %s", options['conf'])

        if service not in config:
            msg = 'No configuration found for %s' % service
            self.stderr.write(msg)
            logger.error(msg)

        service_config = config.pop(service)
        product_no = service_config['product-no']
        try:
            product = Product.get_by_no(product_no)
        except Exception as err:
            logger.error('Product cannot be found: its number is %s. Detail: %s', product_no, err)
            sys.exit(1)

        msg = 'About to ingest contract data of service %s (%s) into the database' % (service, product_no)
        logger.debug(msg)
        self.stdout.write(msg)

        # # load helper data first
        # accounts = load_account_names('../ersa_accounts_20180501.json')
        account_helper = AccountHelper('../ersa_accounts_20180501.json')
        contact_helper = ContactHelper('../ersa_contacts_20180501.json')

        crm_config = service_config['CRM']
        for contract in get_json(crm_config['url']):
            extractor = Extractor(contract)
            try:
                manager_info = extractor.get_contact()
                # Currently, if managerUnit is not a unit in biller, there is a NameError
                parent_account, child_account = create_linked_accounts(manager_info['accounts'], account_helper)
                dynamics_id = contact_helper.get(manager_info['email'])['dynamics_id']
                manager = create_contact(manager_info['name'], manager_info['email'], dynamics_id, child_account)
                # TODO: to confirm how to get info: through extractor or directly
                order_values = extractor.get_order()
                order_values['biller'] = parent_account
                order_values['manager'] = manager
                try:
                    order = create_order(**order_values)
                except Exception as err:
                    logger.error('Cannot create order for %s', str(contract))
                    logger.error(err)
                    continue
            except (KeyError, NameError) as err:
                logger.error('%s, %s', str(err), str(contract))
                continue

            try:
                orderline_info = extractor.get_orderline(crm_config['identifier'])
                create_orderline(order, product, orderline_info)
            except KeyError as err:
                logger.warning('Incomplete orderline data - missing key: %s in %s, %s',
                               err, contract['orderID'], contract['salesorderid'])
