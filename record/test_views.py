# python manage.py test record.test_views --settings=runner.record

from django.test import TestCase, Client

from .views.helpers import VALID_PRODUCTS

class UsageViewTestCase(TestCase):
    def test_required_args_check(self):
        c = Client()
        for product in VALID_PRODUCTS:
            response = c.get('/usage/%s/' % product)
            self.assertEqual(response.status_code, 400)
            response_message = response.json()
            self.assertIn('error', response_message)
            self.assertTrue(response_message['error'].startswith('Missing required query arg'))

    def test_call_product_usage_list_endpoints(self):
        c = Client()
        for product in VALID_PRODUCTS:
            response = c.get('/usage/%s/?start=1&end=10&email=test@ersa.edu.au' % product)
            self.assertEqual(response.status_code, 200)

