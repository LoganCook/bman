# python manage.py test record.test_views --settings=runner.record
from unittest.mock import patch

from django.test import TestCase, Client

from .views.helpers import VALID_PRODUCTS

import record

NOT_EXIST_EMAIL = 'not.exist@some.com'
DUMMY_DYNAMICS_ID = '8b3615e1-4afd-e611-810b-e0071b6685b1'


def required_args_check(tester, usage_or_fee):
    c = Client()
    for product in VALID_PRODUCTS:
        response = c.get('/%s/%s/' % (usage_or_fee, product))
        tester.assertEqual(response.status_code, 400)
        response_message = response.json()
        tester.assertIn('error', response_message)
        tester.assertTrue(response_message['error'].startswith('Missing required query arg'))


def call_fee_or_usage_endpoints(tester, usage_or_fee, email='test@ersa.edu.au', response_code=200):
    c = Client()
    for product in VALID_PRODUCTS:
        response = c.get('/%s/%s/?start=1&end=10&email=%s' % (usage_or_fee, product, email))
        tester.assertEqual(response_code, response.status_code)


def call_fee_or_usage_endpoints_with_invalid_product_no(tester, usage_or_fee, email='test@ersa.edu.au'):
    c = Client()
    response = c.get('/%s/not_validate/?start=1&end=10&email=%s' % (usage_or_fee, email))
    tester.assertEqual(response.status_code, 400)
    tester.assertEqual('Invalid product number', response.json()['error'])


class UsageViewTestCase(TestCase):
    def test_required_args_check(self):
        required_args_check(self, 'usage')

    def test_call_product_usage_list_endpoints(self):
        call_fee_or_usage_endpoints(self, 'usage')

    def test_invalid_product_gets_400(self):
        call_fee_or_usage_endpoints_with_invalid_product_no(self, 'usage')

    def test_get_json_cannot_connect(self):
        with patch('record.models.Contact.get_by_email') as patched_get:
            patched_get.side_effect = record.models.Contact.DoesNotExist
            with self.assertRaises(record.models.Contact.DoesNotExist) as cm:
                record.models.Contact.get_by_email('sdfs')

    def test_not_exist_user(self):
        call_fee_or_usage_endpoints(self, 'fee', NOT_EXIST_EMAIL, 401)


class FeeViewTestCase(TestCase):
    def test_required_args_check(self):
        required_args_check(self, 'fee')

    def test_call_product_fee_list_endpoints(self):
        call_fee_or_usage_endpoints(self, 'fee')

    def test_invalid_fee_gets_400(self):
        call_fee_or_usage_endpoints_with_invalid_product_no(self, 'fee')

    def test_not_exist_user(self):
        call_fee_or_usage_endpoints(self, 'fee', NOT_EXIST_EMAIL, 401)

    def test_summary_by_not_exist_user(self):
        email = NOT_EXIST_EMAIL
        c = Client()
        response = c.get('/fee/summary/?start=1&end=10&email=%s' % email)
        self.assertEqual(response.status_code, 401)

    def _verify_empty_summary(self, email):
        c = Client()
        response = c.get('/fee/summary/?start=1&end=10&email=%s' % email)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_user_gets_empty_summary(self):
        email = 'some.one@good.edu.au'
        biller = record.models.Account.objects.create(name='biller', dynamics_id=DUMMY_DYNAMICS_ID)
        contact = record.models.Contact.objects.create(account_id=biller.pk, dynamics_id=DUMMY_DYNAMICS_ID, name='test', email=email)
        self._verify_empty_summary(email)

    def test_manager_gets_empty_summary(self):
        email = 'some.one@good.edu.au'
        biller = record.models.Account.objects.create(name='biller', dynamics_id=DUMMY_DYNAMICS_ID)
        contact = record.models.Contact.objects.create(account_id=biller.pk, dynamics_id=DUMMY_DYNAMICS_ID, name='test', email=email)
        record.models.Manager.objects.create(account_id=biller.pk, contact_id=contact.pk)
        self._verify_empty_summary(email)
