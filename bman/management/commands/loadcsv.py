import csv
import os

from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from bman.models import *

# Read csv file and create model instances

# keys or columns on 10/02/2016, SQL_Ingest_Test_v1
# 30
#~ [
  #~ "Service - RDS Allocation",
  #~ "Organisation",
  #~ "Location Country",
  #~ "Service - Storage",
  #~ "First Name",
  #~ "Service - HPC",
  #~ "Role",
  #~ "Location City",
  #~ "Username",
  #~ "Role Detail",
  #~ "Insightly ID",
  #~ "Background",
  #~ "User Project Details",
  #~ "ARMS ID",
  #~ "Email Address",
  #~ "Service - RDS Allocation GB",
  #~ "Salutation",
  #~ "LDAP Account creation date",
  #~ "Research Group",
  #~ "Full Name",
  #~ "Supervisor",
  #~ "MobilePhone",
  #~ "Last Name",
  #~ "Location Post Code",
  #~ "DateCreated",
  #~ "School/Department",
  #~ "Business Phone",
  #~ "Service - RDS Allocation #",
  #~ "Location State",
  #~ "Location Street"
#~ ]

#~ keys on 11/02/2016, in total 43
#~ Insightly ID
#~ Salutation
#~ Full Name #ignored
#~ First Name
#~ Last Name

#Create them in order
#~ Organisation
#~ School/Department : relationshiptype: Organisation, Organisation -> School/Department
#~ Research Group : relationshiptype: Organisation, School/Department -> Research Group, if there is not school, go up to Organisation

#~ AD Account ID #ignored

#Create role in the lowest level organisation. Put account to this role.
#~ Role
#~ Role Detail
#~ Email Address
#~ Business Phone
#~ MobilePhone
#~ Location Street #ignored
#~ Location City #ignored
#~ Location State #ignored
#~ Location Post Code #ignored
#~ Location Country #ignored
#~ Background #ignored, where to put?
#~ User Project Details #ignored, where to put?

#~ Username
#~ Billing Organisation #Map to Organisation when create role? For persons come from GOV or internationals visiting

#Extra relationship: Person to person: 'Supervision'
#~ Supervisor

#~ Service - HPC #AccessService
#~ Service - Storage #AccessService
#~ Service - Cloud Allocation #no service defined

#~ Service - RDS Allocation #
#~ RDS Filesystem
#~ RDS Approved GB
#~ RDS Collection Name

#~ ARMS ID
#~ FOR 1
#~ FOR 2
#~ FOR 3
#~ FOR 4
#~ FOR 5
#~ FOR 6

#~ Nectar ID (Keystone)
#~ Tennants
#~ Tennant ID

#~ LDAP Account creation date #ignored, insightly date
#~ DateCreated #ignored, insightly date


PERSON = {'first_name': 'First Name', 'last_name': 'Last Name', 'insightly_id': 'Insightly ID', 'title': 'Salutation'}
ORGANISATION = {'name': 'Organisation'}
#All items is a kind of organisation and order is the level from top to bottom, indirect to direct
ORGANISATION_COLS = ['Organisation', 'School/Department', 'Research Group']
ROLE = {'role': 'Role', 'description': 'Role Detail', 'email': 'Email Address', 'phone': 'Business Phone', 'mobile': 'MobilePhone'}
ACCOUNT = {'billing_org': 'Billing Organisation', 'username': 'Username'}
ACCESS = {'HPC': 'Service - HPC', 'STORAGE': 'Service - Storage'}
RDSFIELDS = {'allocation_num': 'Service - RDS Allocation #', 'filesystem': 'RDS Filesystem',
       'approved_size': 'RDS Approved GB', 'collection_name': 'RDS Collection Name'}
NECTAR = {'tenant': 'Tennants', 'openstack_id': 'Tennant ID'}

def get_normalised_role(role):
    normalised = {'EMPLOYEE': 'Employment', 'STUDENT': 'Study'}
    role = role.upper()
    if role in normalised:
        return normalised[role]
    else:
        raise KeyError


def get_normalised_title(title):
    normalised = {'Dr': 'Dr', 'Prof': 'Prof', 'Assoc Prof': 'APro', 'Ms': 'Ms', 'Mrs': 'Mrs', 'Mr': 'Mr', 'Miss': 'Ms'}
    if title in normalised:
        return normalised[title]
    else:
        return ''

# Not used yet
def get_serialized_data(row, model_name, field_mapping):
    """
    field_mapping: key as field name in the model, value should be column name in csv
    """
    data = {}
    for field in field_mapping.keys():
        data[field] = row[field_mapping[field]]

    return {'model': 'bman.' + model_name, 'fields': data }


def get_model_data(row, field_mapping):
    """
    Filter a row to get demanded fields
    Empty cells are not excluded
    field_mapping: key as field name in the model, value should be column name in csv
    """
    data = {}
    for field in field_mapping.keys():
        if field_mapping[field] in row:
            data[field] = row[field_mapping[field]].strip()

    return data


#get_or_create_xxx functions
def _csv_to_person(csv_row_dict):
    data = get_model_data(csv_row_dict, PERSON)

    if not (data['first_name'] and data['last_name']):
        raise ValueError('Both first and last names have to be presented')

    #Remove empty insightly_id, if it exists, try to convert it to int
    if 'insightly_id' in data and len(data['insightly_id']) == 0:
        del data['insightly_id']
    else:
        try:
            data['insightly_id'] = int(data['insightly_id'])
        except ValueError:
            print('%s cannot be converted into int' % data['insightly_id'])
            del data['insightly_id']
        except Exception as e:
            print(e)
            del data['insightly_id']

    data['title'] = get_normalised_title(data['title'])

    try:
        #there are cases that Person is created first as Supervisor
        person = Person.objects.get(first_name=data['first_name'], last_name=data['last_name'])
        dirty = False
        if 'insightly_id' in data:
            if person.insightly_id:
                raise ValueError('Person %(first_name)s %(last_name)s has already have insightly_id. No update.' % data)
            else:
                person.insightly_id = data['insightly_id']
                dirty = True
        if data['title']:
            person.title = data['title']
        if dirty:
            person.save()
    except Person.DoesNotExist:
        person = Person.objects.create(**data)
    return person

def _apply_organisation_relationship(orgs):
    if len(orgs) < 2:
        return
    rel_type = RelationshipType.objects.get(name='Organisation')
    for i in range(len(orgs)-1):
        Relationship.objects.get_or_create(relationshiptype=rel_type, tail_id=orgs[i].pk, head_id=orgs[i+1].pk)

#Create organisations by there names: columns listed in ORGANISATION_COLS
#Order is important
def _csv_to_organisations(csv_row_dict):
    orgs = []
    for col in ORGANISATION_COLS:
        if csv_row_dict[col].strip():
            org, _ = Organisation.objects.get_or_create(name=csv_row_dict[col])
            # These are in hierachical relationship, so, they cannot appear twice
            if org not in orgs:
                orgs.append(org)
    _apply_organisation_relationship(orgs)
    if len(orgs) == 0:
        raise FieldDoesNotExist("No organisation found in all accepted formats")
    return orgs

def _csv_to_role(csv_row_dict, person, org):
    role = None
    data = get_model_data(csv_row_dict, ROLE)
    role_name = data.pop('role')
    if not role_name:
        raise FieldDoesNotExist("Required Role is not defined")

    try:
        role_name = get_normalised_role(role_name)
        rel_type = RelationshipType.objects.get(name=role_name)
        role, _ = Role.objects.get_or_create(person=person, organisation=org, relationshiptype=rel_type, **data)
        return role
    except KeyError:
        print('Role normalisation failed: %s' % role_name)
    except RelationshipType.DoesNotExist:
        print('%s has to be created in the system before a Person can be assined to it' % role_name)
    except Exception as e:
        print("Cannot create role, see below details:")
        print(e)

    raise Exception("Role was not created or found")

def _csv_to_account(csv_row_dict, role):
    data = get_model_data(csv_row_dict, ACCOUNT)
    if data['username']:
        data['billing_org'], _ = Organisation.objects.get_or_create(name=data['billing_org'])
        account, _ = Account.objects.get_or_create(role=role, **data)
        return account
    else:
        return None

import re
FIRST_NAME = re.compile(r"^[A-Z][ \'\w-]+$")
LAST_NAME = re.compile(r"^[A-Za-z][ \'\w-]+$")

SUPERVISOR_TYPE = RelationshipType.objects.get(name='Employment')
def _csv_to_supervisor(csv_row_dict, student):
    #Supervisor column is full of free text, so be picky
    supervisor_cell = csv_row_dict['Supervisor']
    if not supervisor_cell:
        return

    try:
        first_name, last_name = supervisor_cell.split(' ')[-2:]
        if FIRST_NAME.match(first_name) and LAST_NAME.match(last_name):
            # If there are more than one Person has the same name, get will fail to retrive as it expects ONLY one
            # check Employment role?
            supervisor, _ = Person.objects.get_or_create(first_name=first_name, last_name=last_name)
            try:
                employee = supervisor.role_set.get(relationshiptype=SUPERVISOR_TYPE)
                rel_type = RelationshipType.objects.get(name='Supervision')
                Relationship.objects.get_or_create(relationshiptype=rel_type, tail_id=employee.pk, head_id=student.pk)
            except Exception as e:
                raise ValueError('Cannot find a suitable supervisor in empolyment relationship with an organisation. Error: %s' % str(e))
        else:
            raise ValueError('First or last name of supervisor does not meet the standard')
    except Exception as e:
        raise FieldDoesNotExist('Cannot create or use %s as supervisor for %s. \n\t%s' % (supervisor_cell, student.person.full_name, str(e)))

ALLOCATION_NUM = re.compile(r"[A-Z]+[0-9]+")
def _csv_to_services(csv_row_dict, role, access_services):
    data = get_model_data(csv_row_dict, ACCESS)
    for k in access_services.keys():
        if data[k].upper() == k:
            AccessService.objects.get_or_create(catalog=access_services[k], contractor=role)

    data = get_model_data(csv_row_dict, RDSFIELDS)
    if ALLOCATION_NUM.match(data['allocation_num']):
        try:
            data['approved_size'] = int(data['approved_size'])
        except Exception:
            data['approved_size'] = 0
        RDS.objects.get_or_create(contractor=role, **data)

    data = get_model_data(csv_row_dict, NECTAR)
    # As long as there is tenant name, ingest it
    if len(data['tenant']):
        Nectar.objects.get_or_create(contractor=role, **data)

def _load(fn):
      rows = []
      with open(fn, 'r') as csvfile:
        spamreader = csv.DictReader(csvfile)
        for row in spamreader:
            rows.append(row)

      access_services = {'HPC': Catalog.objects.get(name='HPC'),
                          'STORAGE': Catalog.objects.get(name='Storage')}
      cache = []
      for row in rows:
        try:
            orgs = _csv_to_organisations(row)
            person = _csv_to_person(row)
            role = _csv_to_role(row, person, orgs[-1])
            _csv_to_services(row, role, access_services)
            _csv_to_account(row, role)
            cache.append((row, role))
        except Exception as e:
            print('Cannot create model: %s' % e)
            print('Insightly_ID=%(Insightly ID)s, email=%(Email Address)s, name=%(Full Name)s, username=%(Username)s\n' % row)

      #After all persons have been loaded, try to hook up with supervisor
      for row, role in cache:
        try:
            _csv_to_supervisor(row, role)
        except Exception as e:
            print('Fail to establish supervison relationship: %s' % e)
            print('Insightly_ID=%(Insightly ID)s, email=%(Email Address)s, name=%(Full Name)s, username=%(Username)s\n' % row)

class Command(BaseCommand):
    help = 'Load data from a csv file and put them into the database'

    def add_arguments(self, parser):
        parser.add_argument('file_name')

        parser.add_argument('-m', '--model',
            action='append',
            dest='models',
            help='Only load data for specifid models')

    def handle(self, *args, **options):
        if not os.path.exists(options['file_name']):
            raise CommandError('File "%s" does not exist' % options['file_name'])

        self.stdout.write('About to load the data in "%s" into the database' % options['file_name'])

        if options['models']:
            self.stdout.write(str(options['models']))

        _load(options['file_name'])

