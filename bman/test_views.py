"""
Unit tests for views.
"""
import json
from django.test import TestCase, Client

from bman.models import Person

class ViewTestCase(TestCase):
    def setUp(self):
        Person.objects.create(first_name="John", last_name="Smith")
        Person.objects.create(first_name="John Brother", last_name="Smith")

    def test_get_allowed_form(self):
        c = Client()
        response = c.get('/forms/Relationship/')
        self.assertEqual(response.status_code, 200)
        response = c.get('/forms/relationship/')
        self.assertEqual(response.status_code, 200)

    def test_get_not_allowed_form(self):
        c = Client()
        response = c.get('/forms/relationshipform/')
        self.assertEqual(response.status_code, 400)

    def test_get_objects(self):
        c = Client()
        response = c.get('/objects/Relationship/')
        self.assertEqual(response.status_code, 200)

    def test_get_object(self):
        #Only test url and view. Do not care instance yet
        from django.core.exceptions import ObjectDoesNotExist
        c = Client()
        response = c.get('/objects/Person/1/')
        self.assertEqual(response.status_code, 200)

    def test_api_post_with_id_not_allowed(self):
        c = Client()
        response = c.post('/api/person/100/')
        self.assertEqual(response.status_code, 405)

    def test_api_without_id_not_allowed(self):
        c = Client()
        response = c.put('/api/person/')
        self.assertEqual(response.status_code, 400)

        response = c.delete('/api/person/')
        self.assertEqual(response.status_code, 400)

    def test_api_get_object(self):
        c = Client()
        response = c.get('/api/person/1/')
        self.assertEqual(response.status_code, 200)
        person = json.loads(str(response.content,'utf-8'))
        self.assertEqual(person['first_name'], 'John')
        self.assertEqual(person['last_name'], 'Smith')

    def test_api_get_objects(self):
        c = Client()
        response = c.get('/api/person/')
        self.assertEqual(response.status_code, 200)
        persons = json.loads(str(response.content,'utf-8'))
        self.assertEqual(len(persons), 2)

    def test_api_call_with_args(self):
        from bman.models import Organisation
        c = Client()
        response = c.get('/api/person/1/get_service/?name=nectar')
        self.assertEqual(response.status_code, 200)

    def test_api_call_to_model_with_args(self):
        from bman.models import Organisation
        c = Client()
        response = c.get('/api/person/?last_name=Smith')
        self.assertEqual(response.status_code, 200)
        persons = json.loads(str(response.content,'utf-8'))
        for person in persons:
            self.assertEqual(person['last_name'], 'Smith')
