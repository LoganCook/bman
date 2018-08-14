# python manage.py test record.test_ingesters --settings=runner.record

from django.test import TestCase

from record.models import Account, Contact, Order, Orderline, Product, Price
from record.models import HpcUsage, StorageUsage, Tangocloudvm
from record.management.ingesters.base import UsageConfiguration, UsageIngester, YEAR_IN_SECONDS
from record.management.ingesters import TangocloudvmIngester

DUMMY_DYNAMICS_ID = '8b3615e1-4afd-e611-810b-e0071b6685b1'
PRICE_LIST_NAME = "Member's price"
PRODUCT_NO = '0000'
BILLING_START = 1451568600
BILLING_END = 1454246999


class IngesterTestCase(TestCase):
    def setUp(self):
        self.biller = Account.objects.create(name='biller', dynamics_id=DUMMY_DYNAMICS_ID)
        self.contact = Contact.objects.create(
            account_id=self.biller.pk,
            dynamics_id=DUMMY_DYNAMICS_ID,
            name='test manager',
            email='test.manager@ersa.edu.au')

    def create_order(self, product_type):
        order = Order.objects.create(
            name='test order',
            no="unique eRSA no",
            description="description",
            dynamics_id=DUMMY_DYNAMICS_ID,
            price_list=PRICE_LIST_NAME,
            biller=self.biller,
            manager=self.contact)

        demo_product = Product.objects.create(name='hpc demo',
                                              dynamics_id='1234',
                                              no=PRODUCT_NO,
                                              structure='Product',
                                              type=product_type)
        # price effective from 1/1/2016
        Price.objects.create(product=demo_product, list_name=PRICE_LIST_NAME, dynamics_id=DUMMY_DYNAMICS_ID, unit='Any unit', amount=1200, date=1451568600)
        prices = demo_product.get_prices()
        self.assertEqual(1, len(prices))
        self.assertEqual(1200, prices[0].amount)

        Orderline.objects.create(order=order, product=demo_product, quantity=1, price=1, identifier='identifier1')

    def test_calculate_sales_inventory_fee(self):
        self.create_order('Sales Inventory')

        usage_source = {
            "orderline_id": 1,
            "start": "1451568600",
            "end": "1454246999",
            "partition": "p1",
            "cpu_seconds": 3600,
            "count": 1
        }

        HpcUsage.objects.create(**usage_source)

        product = Product.get_by_no(PRODUCT_NO)
        yearly_price = product.get_price(PRICE_LIST_NAME)

        usage_conf = {
            "original-data": {
                "url": "http://url/hpc",
                "headers": {
                    "x-ersa-auth-token": "11111111-2222-3333-4444-555555555555"
                }
            },
            "orderline": {
                "crm-linker": "owner",
                "aggregators": ["partition"]
            },
            "fields": {
                "partition": "partition",
                "cpu_seconds": "cpu_seconds",
                "job_count": "count"
            },
            "fee-field": "cpu_seconds"
        }
        usage_config = UsageConfiguration(PRODUCT_NO, usage_conf)
        calculator = UsageIngester(usage_config)

        usage = HpcUsage.get(BILLING_START, BILLING_END).filter(orderline_id=1).select_related('orderline')[0]

        fee = calculator.calculate_fee(usage, BILLING_START, BILLING_END)
        fee_should_be = usage.cpu_seconds * yearly_price / YEAR_IN_SECONDS
        self.assertEqual(fee_should_be, fee)

    def test_calculate_services_fee(self):
        self.create_order('Services')

        usage_source = {
            "orderline_id": 1,
            "start": "1451568600",
            "end": "1454246999",
            "usage": 1543
        }

        StorageUsage.objects.create(**usage_source)

        product = Product.get_by_no(PRODUCT_NO)
        yearly_price = product.get_price(PRICE_LIST_NAME)

        usage_conf = {
            "original-data": {
                "url": "http://url/storage",
                "headers": {
                    "x-ersa-auth-token": "11111111-2222-3333-4444-555555555555"
                }
            },
            "orderline": {
                "crm-linker": "owner"
            },
            "fields": {
                "usage": "usage"
            },
            "fee-field": "usage"
        }
        usage_config = UsageConfiguration(PRODUCT_NO, usage_conf)
        calculator = UsageIngester(usage_config)

        usage = StorageUsage.get(BILLING_START, BILLING_END).filter(orderline_id=1).select_related('orderline')[0]

        fee = calculator.calculate_fee(usage, BILLING_START, BILLING_END)
        fee_should_be = (usage.end - usage.start) * yearly_price / YEAR_IN_SECONDS * usage.usage
        self.assertEqual(fee_should_be, fee)

    def test_update_tangocloudvm_os(self):
        usage_source = {
            'ram': 12,
            'id': 'vm-13619',
            'businessUnit': 'FUSA',
            'storage': 228.956340777538,
            'server': 'yang-pcehr-prod',
            'uptimePercent': 99.4323099151235,
            'span': 715,
            'core': 4,
            'os': 'CentOS 4/5 or later (64-bit)'}

        usage_conf = {
            "original-data": {
                "url": "http://url/storage",
                "headers": {
                    "x-ersa-auth-token": "11111111-2222-3333-4444-555555555555"
                }
            },
            "fields": {
                "storage": "storage",
                "span": "span",
                "uptimePercent": "uptime_percent"
            },
            "orderline": {
                "crm-linker": "id",
                "extra": {
                    "id": "server_id",
                    "server": "server",
                    "core": "core",
                    "ram": "ram",
                    "os": "os",
                    "businessUnit": "business_unit"
                }
            },
            "fee-field": "core"
        }

        self.create_order('Services')

        usage_config = UsageConfiguration(PRODUCT_NO, usage_conf)
        ingester = TangocloudvmIngester(usage_config)
        self.assertIsInstance(ingester, UsageIngester)

        orderline = Orderline.objects.get(id=1)
        ingester.save_config(orderline, usage_source)
        config = Tangocloudvm.objects.get(orderline_id=orderline.id)
        self.assertIsInstance(config, Tangocloudvm)

        usage_source['os'] = 'change os cause unique constrain failure'
        ingester.save_config(orderline, usage_source)
        config = Tangocloudvm.objects.get(orderline_id=orderline.id)
        self.assertIsInstance(config, Tangocloudvm)
        self.assertEqual('change os cause unique constrain failure', config.os)
