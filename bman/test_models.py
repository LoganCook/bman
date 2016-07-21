from django.core.exceptions import ValidationError
from django.test import TestCase

from bman.models import *

class PersonTestCase(TestCase):
    def setUp(self):
        Person.objects.create(first_name="John", last_name="Smith")

    def test_person(self):
        john = Person.objects.get(first_name="John")
        self.assertIsInstance(john, Person)

class OrganisationTestCase(TestCase):
    def setUp(self):
        Organisation.objects.create(name="University of Adelaide")

    def test_organisation(self):
        uofa = Organisation.objects.get(name="University of Adelaide")
        self.assertIsInstance(uofa, Organisation)

    def test_get_tops(self):
        rel_type = RelationshipType.objects.create(name='Organisation',
            entity_tail = 'organisation',
            entity_head = 'organisation',
            forward='is the parent organisation of',
            backward='is a sub-organisation of')
        Organisation.objects.create(name="A School of University of Adelaide")
        Relationship.objects.create(tail_id=1, head_id=2, relationshiptype=rel_type)
        self.assertEqual(len(Organisation.get_tops()), 1)

class RelationshipTypeTestCase(TestCase):
    def test_validations(self):
        ins = dict(name='Employment',
            entity_tail='organisation',
            entity_head='person',
            forward='manages',
            backward='works for')

        for k in ins.keys():
            ill_ins = ins.copy()
            del ill_ins[k]
            r = RelationshipType(**ill_ins)
            self.assertRaises(ValidationError, r.full_clean)

        #All entities have to be in the RelationshipType.ENTITY
        for k in ['entity_tail', 'entity_head']:
            ill_ins = ins.copy()
            ill_ins[k] = 'something bad'
            r = RelationshipType(**ill_ins)
            self.assertRaises(ValidationError, r.full_clean)

class RoleTestCase(TestCase):
    def test_role_creation(self):
        rt = RelationshipType.objects.create(name='Employment',
            entity_tail = 'organisation',
            entity_head = 'person',
            forward = 'manages',
            backward = 'works for')
        p = Person.objects.create(first_name='John', last_name='Smith', title='Dr')
        o = Organisation.objects.create(name='University of Adelaide')

        role = Role(person_id=1, organisation_id=1, relationshiptype=RelationshipType.objects.get(name='Employment'))
        self.assertEqual(str(role), 'University of Adelaide manages Dr John Smith')
        self.assertEqual(role.backward, 'Dr John Smith works for University of Adelaide')

class RelationshipTestCase(TestCase):
    def test_role_creation(self):
        rt = RelationshipType.objects.create(name='Employment',
            entity_tail = 'organisation',
            entity_head = 'person',
            forward = 'manages',
            backward = 'works for')
        p = Person.objects.create(first_name='John', last_name='Smith', title='Dr')
        o = Organisation.objects.create(name='University of Adelaide')

        #Two different ways to create instances
        role1 = Relationship(tail_id=1, head_id=1, relationshiptype=rt)
        self.assertEqual(str(role1), 'University of Adelaide manages Dr John Smith')

        role2 = Relationship.objects.create(tail_id=o.pk, head_id=p.pk, relationshiptype='Employment')
        self.assertEqual(str(role2), 'University of Adelaide manages Dr John Smith')

##This is a to-do: how to properly test signal has been received and record?
#class EventTestCase(TestCase):
#    def test_register_person_created(self):
#        john = Person.objects.create(first_name="John", last_name="Smith")
#        self.assertIsInstance(john, Person)
#        john.save()
#        et = EventType.objects.create(name='create',entity='person')
#        print(et)
#        e = Event.objects.create(type=et, entity_id=john.id)
#        print(e)

class ServiceTestCase(TestCase):
    fixtures = ['catalog.json']
    def setUp(self):
        rt = RelationshipType.objects.create(name='Employment',
            entity_tail = 'organisation',
            entity_head = 'person',
            forward = 'manages',
            backward = 'works for')
        p = Person.objects.create(first_name='John', last_name='Smith', title='Dr')
        o = Organisation.objects.create(name='University of Adelaide')

        role = Role.objects.create(person_id=1, organisation_id=1, relationshiptype=RelationshipType.objects.get(name='Employment'))
        Account.objects.create(role=role, username='goodtester', billing_org=o)
        AccessService.objects.create(catalog=Catalog.objects.get(pk=1), contractor=role)

    def test_organisation_services(self):
        uofa = Organisation.objects.get(name="University of Adelaide")
        self.assertTrue(len(uofa.get_all_services()) > 0)

    def test_person_services(self):
        p = Person.objects.get(first_name='John', last_name='Smith')
        self.assertTrue(len(p.get_all_services()) > 0)

    def test_organisation_to_a_service(self):
        uofa = Organisation.objects.get(name="University of Adelaide")
        self.assertEqual(len(uofa.get_service('AccessService')), 1)
        self.assertEqual(len(uofa.get_service('NotExist')), 0)

    def test_person_to_a_service(self):
        p = Person.objects.get(first_name='John', last_name='Smith')
        self.assertIsInstance(p.get_service('AccessService')[0], AccessService)
        self.assertEqual(len(p.get_service('NotExist')), 0)
