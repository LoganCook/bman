# python manage.py test record.test_models --settings=runner.record
import datetime
import json

from django.test import TestCase

from record.models import Account, Contact, Product, Order, Orderline, Price, Fee
from record.models.tango_vm import Tangocloudvm, TangocloudvmUsage


DUMMY_DYNAMICS_ID = '8b3615e1-4afd-e611-810b-e0071b6685b1'


class AccountTestCase(TestCase):
    # Update these values when TEST_DATA_FILE has been changed

    TOP_ACCOUNT = 'University of Adelaide'

    def setUp(self):
        top = Account.objects.create(name=self.TOP_ACCOUNT, dynamics_id=DUMMY_DYNAMICS_ID)
        Account.objects.create(name="School of A", dynamics_id=DUMMY_DYNAMICS_ID, parent_id=top.pk)

    def test_top(self):
        tops = Account.get_tops()
        self.assertEqual(1, len(tops))
        self.assertEqual(self.TOP_ACCOUNT, tops[0].name)

    def test_children_of(self):
        top = Account.objects.get(name=self.TOP_ACCOUNT)
        children = Account.get_children_of(top.pk)
        self.assertEqual(1, len(children))

    def test_children(self):
        top = Account.objects.get(name=self.TOP_ACCOUNT)
        children = top.children
        self.assertEqual(1, len(children))

    def test_hierarchy(self):
        hierarchy = Account.get_hierarchy()
        self.assertEqual(1, len(hierarchy.keys()))
        self.assertEqual(1, len(hierarchy[self.TOP_ACCOUNT]['children']))

    def test_only_top_account_can_have_managers(self):
        top = Account.objects.get(name=self.TOP_ACCOUNT)
        child = top.children[0]
        with self.assertRaises(TypeError):
            child.assign_manager(None)

        contact = Contact.objects.create(account_id=top.pk, dynamics_id=DUMMY_DYNAMICS_ID, name='test manager', email='test.manager@ersa.edu.au')
        top.assign_manager(contact)
        self.assertTrue(top.has_manager(contact))


class ContactTestCase(TestCase):
    def test_create_contact(self):
        biller = Account.objects.create(name='biller', dynamics_id=DUMMY_DYNAMICS_ID)
        contact = Contact.objects.create(account_id=biller.pk, dynamics_id=DUMMY_DYNAMICS_ID, name='test', email='some.good@ersa.edu.au')
        retrieved = Contact.objects.get(dynamics_id=DUMMY_DYNAMICS_ID)
        self.assertEqual(contact, retrieved)


class ProductTestCase(TestCase):
    def test_create_product(self):
        prod_composed_name = 'product composed'
        prod_simple_name = 'product simple or part'
        prod_no = 'simpleprod'
        prod_type = 'Services'
        simple = Product.objects.create(name=prod_simple_name, dynamics_id=DUMMY_DYNAMICS_ID, no=prod_no, type=prod_type)
        retrieved = Product.objects.get(name=prod_simple_name)
        self.assertEqual(simple, retrieved)
        self.assertEqual('%s, type=%s, (%s)' % (prod_simple_name, prod_type, prod_no), str(simple))

        composed = Product.objects.create(name=prod_composed_name, dynamics_id=DUMMY_DYNAMICS_ID, no='simpleprod', type=prod_type)
        retrieved = Product.objects.get(name=prod_composed_name)
        simple.parent = composed
        simple.save()
        self.assertEqual('%s, type=%s, (%s), composed part' % (prod_simple_name, prod_type, prod_no), str(simple))
        self.assertTrue(composed.is_composed)


class OrderTestCase(TestCase):
    manager_email = 'test.manager@ersa.edu.au'

    def setUp(self):
        biller = Account.objects.create(name='biller', dynamics_id=DUMMY_DYNAMICS_ID)
        contact = Contact.objects.create(account_id=biller.pk, dynamics_id=DUMMY_DYNAMICS_ID, name='test manager', email=self.manager_email)
        Order.objects.create(name='test order', dynamics_id=DUMMY_DYNAMICS_ID, biller=biller, manager=contact)

    def test_create_order(self):
        biller = Account.objects.get(name='biller')
        order = Order.objects.get(name='test order')
        self.assertEqual(order, biller.orders[0])
        self.assertTrue(order.record_date > 1524712589)

    def test_get_details(self):
        order = Order.objects.get(name='test order')
        demo_product, _ = Product.objects.get_or_create(name='demo product', dynamics_id=DUMMY_DYNAMICS_ID)
        # There can be more lines for the same product
        Orderline.objects.create(order=order, product=demo_product, quantity=1, price=1, identifier='identifier1')
        Orderline.objects.create(order=order, product=demo_product, quantity=1, price=10, identifier='identifier2')

        another_product, _ = Product.objects.get_or_create(name='demo product 2', dynamics_id=DUMMY_DYNAMICS_ID)
        Orderline.objects.create(order=order, product=another_product, quantity=1, price=10, identifier='identifier2')

        orderlines = order.orderlines
        self.assertEqual(3, len(orderlines))
        demo_product_orderlines = order.get_orderlines_by_product(demo_product)
        self.assertEqual(2, len(demo_product_orderlines))


class PriceTestCase(TestCase):
    def test_price_of_one_product(self):
        initial_price, final_price = 23.35, 25.35
        start_timestamp = int(datetime.datetime.now().timestamp())
        span_in_seconds = 100
        demo_product = Product.objects.create(name='demo product', dynamics_id=DUMMY_DYNAMICS_ID)
        Price.objects.create(product=demo_product, list_name="Member's price", dynamics_id=DUMMY_DYNAMICS_ID, unit='GB', amount=initial_price, date=start_timestamp)
        Price.objects.create(product=demo_product, list_name="Member's price", dynamics_id=DUMMY_DYNAMICS_ID, unit='GB', amount=final_price, date=start_timestamp + span_in_seconds)

        prices = demo_product.get_prices()
        self.assertEqual(2, len(prices))

        history = demo_product.get_historical_prices(start_timestamp, start_timestamp + span_in_seconds)
        self.assertEqual(1, len(history))

        self.assertEqual(prices[0], history[0])


class TangocloudvmTestCase(TestCase):

    vms = None
    product = None

    def setUp(self):
        biller = Account.objects.create(name='biller', dynamics_id=DUMMY_DYNAMICS_ID)
        contact = Contact.objects.create(account_id=biller.pk, dynamics_id=DUMMY_DYNAMICS_ID, name='test manager', email='some@ersa.edu.au')
        order = Order.objects.create(name='test order', dynamics_id=DUMMY_DYNAMICS_ID, biller=biller, manager=contact)
        self.product = Product.objects.create(name='tangocloudvm', dynamics_id=DUMMY_DYNAMICS_ID)

        # data are from /vms/instance?end=1522502999&start=1519824600
        with open('record/TangoCloudUsage.json', 'r') as jf:
            self.vms = json.load(jf)
        for vm in self.vms:
            orderline = Orderline.objects.create(order=order, product=self.product, quantity=1, price=1, identifier=vm['id'])
            Tangocloudvm.objects.create(orderline=orderline,
                                        server_id=vm['id'],
                                        server=vm['server'],
                                        core=vm['core'],
                                        ram=vm['ram'],
                                        os=vm['os'],
                                        business_unit=vm['businessUnit'])
        self.assertEqual(len(self.vms), Tangocloudvm.objects.count())

    def test_record_usage(self):
        vm = self.vms[0]
        orderline = Orderline.objects.get(identifier=vm['id'])
        start_timestamp, end_timestamp = 1522502999, 1519824600
        TangocloudvmUsage.objects.create(orderline=orderline,
                                         start=start_timestamp,
                                         end=end_timestamp,
                                         storage=vm['storage'],
                                         span=vm['span'],
                                         uptime_percent=vm['uptimePercent'])

        vm_config = Tangocloudvm.objects.get(pk=vm['id'])
        Fee.objects.create(orderline=orderline,
                           start=start_timestamp,
                           end=end_timestamp,
                           amount=vm_config.core * 200 + vm_config.ram * 10)
        future_seconds = 10000
        TangocloudvmUsage.objects.create(orderline=orderline,
                                         start=start_timestamp + future_seconds,
                                         end=end_timestamp + future_seconds,
                                         storage=vm['storage'],
                                         span=vm['span'],
                                         uptime_percent=vm['uptimePercent'])
        Fee.objects.create(orderline=orderline,
                           start=start_timestamp + future_seconds,
                           end=end_timestamp + future_seconds,
                           amount=vm_config.core * 200 + vm_config.ram * 10)

        self.assertEqual(2, TangocloudvmUsage.objects.count())
        self.assertEqual(2, Fee.of_product(self.product).count())

    def test_calculate_fee(self):
        vm = self.vms[0]
        orderline = Orderline.objects.get(identifier=vm['id'])
        start_timestamp, end_timestamp = 1522502999, 1519824600
        usages = TangocloudvmUsage.objects.filter(orderline=orderline)

        amount = 0

        for usage in usages:
            amount = amount + usage.span * 100
            if usage.start < start_timestamp:
                start_timestamp = usage.start
            if usage.end > end_timestamp:
                end_timestamp = usage.end

        Fee.objects.create(orderline=orderline,
                           start=start_timestamp,
                           end=end_timestamp,
                           amount=amount)

        retrieved = Fee.objects.get(orderline=orderline,
                                    start=start_timestamp,
                                    end=end_timestamp)

        self.assertEqual(amount, retrieved.amount)
