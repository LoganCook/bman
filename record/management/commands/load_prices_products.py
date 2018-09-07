"""
Ingest usage json created by reporting-unified.usage
"""

import logging
import json

from django.core.management.base import BaseCommand

from date_helpers import date_string_to_timestamp
from record.models import Product, Price
from ..utils import get_json
from ..utils.command_helper import setup_logger

setup_logger(__name__)
logger = logging.getLogger('record.management')


class Command(BaseCommand):
    help = 'Ingest data from a BMAN and usage endpoints'

    def add_arguments(self, parser):
        parser.add_argument('--url', help='url of endpoint of pricelist API')
        parser.add_argument('--file', help='file of pricelist')
        parser.add_argument('-d', '--date', help='Date of prices are valid from (%%Y%%m%%d)')

    def handle(self, *args, **options):
        # /api/pricelist/
        # {
        #     "pricelevel": "Members Price List",
        #     "uomid": "b65f38c4-464c-428a-b67e-274fa06d7a7f",
        #     "_transactioncurrencyid_value@OData.Community.Display.V1.FormattedValue": "Australian Dollar",
        #     "amount": 2000,
        #     "@odata.etag": "W/\"4718419\"",
        #     "productstructure": "Product",
        #     "producttype": "Sales Inventory",
        #     "amount@OData.Community.Display.V1.FormattedValue": "$2000.00",
        #     "productnumber": "HVM0001",
        #     "product": "Hosted VM Server",
        #     "_transactioncurrencyid_value": "744fd97c-18fb-e511-80d8-c4346bc5b718",
        #     "productid": "9ce0a095-fe39-e711-8122-70106fa3d971",
        #     "pricelevelid": "0c407dd9-1b59-e611-80e2-c4346bc58784",
        #     "uom": "Primary Unit",
        #     "productpricelevelid": "57f4b762-023a-e711-8122-70106fa3d971"
        # },

        def create_product(content):
            product, _ = Product.objects.get_or_create(name=content['product'],
                                                       dynamics_id=content['productid'],
                                                       no=content['productnumber'],
                                                       structure=content['productstructure'],
                                                       type=content['producttype'])
            return product

        def create_price(content, product, valid_ts=None):
            fields = {
                "product": product,
                "list_name": content['pricelevel'],
                "dynamics_id": content['productpricelevelid'],
                "unit": content['uom'],
                "amount": content['amount']
            }
            if valid_ts:
                fields['date'] = valid_ts

            price, _ = Price.objects.get_or_create(**fields)
            return price

        valid_ts = None

        # Get prices from either a URL or a file
        prices = None
        if options['url'] is not None:
            prices = get_json(options['url'])
        elif options['file'] is not None:
            with open(options['file'], 'r') as jf:
                prices = json.load(jf)

        if options['date']:
            valid_ts = date_string_to_timestamp(options['date'])
        fields = ('pricelevel', 'productpricelevelid', 'productid', 'product',
                  'productnumber', 'uom', 'amount', 'productstructure', 'producttype')

        for price in prices:
            for field in fields:
                logger.info('%s: %s', field, price[field])
            current_product = create_product(price)
            create_price(price, current_product, valid_ts)
