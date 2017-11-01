"""
Unit tests for views.
"""

# python manage.py test dynamicsp.test_views --sett runner.dynamicsp
# FIXME: need to mockup a few things before these can be unit tests

import json
from django.test import SimpleTestCase, Client

class ViewTestCase(SimpleTestCase):
    def test_organisation(self):
        c = Client()
        response = c.get('/api/organisation/')
        self.assertEqual(response.status_code, 200)
        response = c.get('/api/organisation/?method=get_tops')
        self.assertEqual(response.status_code, 200)
        response = c.get('/api/organisation/uuid-susm-udss-uud/get_service/?name=nectar')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), [])
        response = c.get('/api/organisation/uuid-susm-udss-uud/get_service/')
        self.assertJSONEqual(response.content.decode('utf-8'), [])
        self.assertEqual(response.status_code, 200)
        response = c.get('/api/organisation/uuid-susm-udss-uud/get_service/?name=nectar')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), [])

    def test_startup(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)
        services = json.loads(response.content.decode('utf-8'))
        self.assertTrue('organisation' in services)
        self.assertGreater(len(services), 1)

    def test_contract(self):
        c = Client()
        response = c.get('/api/v2/contract/')
        self.assertEqual(response.status_code, 404)
        response = c.get('/api/v2/contract/nonexist/')
        self.assertEqual(response.status_code, 400)
        print(response.content.decode('utf-8'))
        response = c.get('/api/v2/contract/tangocompute/')
        self.assertEqual(response.status_code, 200)
        service = json.loads(response.content.decode('utf-8'))
        self.assertTrue(isinstance(service, list))
