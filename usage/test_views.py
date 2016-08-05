"""
Unit tests for views.
"""
import json
from django.test import TestCase, Client
from django.core.management import call_command


class ViewTestCase(TestCase):
    TEST_DATA_FILE = 'usage/nova_1470148200_1470320999.json'
    # Update these values when TEST_DATA_FILE has been changed
    EARLIEST = '1470148200'
    TOTAL = 3  # records with no manager in NovaUsage will not be ingested
    CLASS_ONE_COUNT = 3
    CLASS_TWO_COUNT = 2
    CLASS_THREE_COUNT = 1

    @classmethod
    def setUpTestData(cls):
        call_command('ingest', cls.TEST_DATA_FILE, type='nova')
        with open(cls.TEST_DATA_FILE, 'r') as jf:
            cls.data = json.load(jf)

    def test_single_obj_not_allowed(self):
        c = Client()
        response = c.post('/objects/novausage/1/')
        self.assertEqual(response.status_code, 405)

    def test_get_objects(self):
        c = Client()
        response = c.get('/objects/novausage/')
        self.assertEqual(response.status_code, 200)

    def test_get_objects_with_method(self):
        c = Client()
        response = c.get('/objects/novausage/summarise/')
        self.assertEqual(response.status_code, 200)

    def test_api_single_obj_not_allowed(self):
        c = Client()
        response = c.post('/api/novausage/1/')
        self.assertEqual(response.status_code, 405)

    def test_api_get_objects(self):
        c = Client()
        response = c.get('/api/novausage/')
        self.assertEqual(response.status_code, 200)
        usages = json.loads(str(response.content, 'utf-8'))
        self.assertEqual(len(usages), self.TOTAL)

    def test_api_call_to_model_with_args(self):
        c = Client()
        response = c.get('/api/novausage/?class_one=1')
        self.assertEqual(response.status_code, 200)
        usages = json.loads(str(response.content, 'utf-8'))
        for usage in usages:
            self.assertEqual(usage['class_one'], 1)

    def test_api_method_call_with_args(self):
        c = Client()
        response = c.get('/api/novausage/summarise/?start=' + self.EARLIEST)
        self.assertEqual(response.status_code, 200)
        usages = json.loads(str(response.content, 'utf-8'))
        self.assertEqual(len(usages), self.TOTAL)

    def test_api_method_call_with_list_args(self):
        c = Client()
        response = c.get('/api/novausage/summarise/?classifiers=University')
        self.assertEqual(response.status_code, 200)
        usages = json.loads(str(response.content, 'utf-8'))
        self.assertEqual(len(usages), self.CLASS_ONE_COUNT)

        response = c.get('/api/novausage/summarise/?classifiers=University&classifiers=School')
        self.assertEqual(response.status_code, 200)
        usages = json.loads(str(response.content, 'utf-8'))
        self.assertEqual(len(usages), self.CLASS_TWO_COUNT)

        response = c.get('/api/novausage/summarise/?classifiers=University&classifiers=School&classifiers=Group')
        self.assertEqual(response.status_code, 200)
        usages = json.loads(str(response.content, 'utf-8'))
        self.assertEqual(len(usages), self.CLASS_THREE_COUNT)
