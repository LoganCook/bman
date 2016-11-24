import os
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from bman.models import Role, Nectar, RDS
from bman.management.importers import NectarTenantImporter, RDSImporter

logger = logging.getLogger('bman.management')

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)


def import_nectar_tentants(options, stdout, stderr):
    """Nectar cloud service records: tenants(projects) and managers"""
    importer = NectarTenantImporter(options['file_name'])
    projects = importer.projects
    stdout.write('Read %d projects' % len(projects))

    for tenant, managers in projects:
        in_db = Nectar.objects.filter(openstack_id=tenant['openstack_id']).exists()
        if in_db:
            stderr.write('%(tenant)s %(openstack_id)s alread exisits. No more action.' % tenant)
            continue

        if len(managers) > 1:
            stderr.write('Multiple managers found for %(tenant)s - only one is allowed.' % tenant)
            continue

        try:
            mr = Role.objects.get(email=managers[0]['email'])
            Nectar.objects.get_or_create(contractor=mr, **tenant)
        except ObjectDoesNotExist:
            stderr.write('Role of manager identified by %s is not in the system. Create it first' % managers[0]['email'])
        except Exception as err:
            logging.exception('Cannot ingest tenant: %s because %s', str(tenant), err)


def import_rds(options, stdout, stderr):
    """RDS service records"""
    importer = RDSImporter(options['file_name'])
    services = importer.services
    stdout.write('Read %d service records' % len(services))

    for service in services:
        in_db = RDS.objects.filter(filesystem=service['filesystem']).exists()
        if in_db:
            stderr.write('RDS service record of %s alread exisits. No more action.' % service['filesystem'])
            continue

        try:
            mr = Role.objects.get(email=service['email'])
            del service['email']
            RDS.objects.get_or_create(contractor=mr, **service)
        except ObjectDoesNotExist:
            stderr.write('Role of manager identified by %s is not in the system. Create it first' % service['email'])
        except Exception as err:
            logging.exception('Cannot ingest service: %s because %s', str(service), err)


importers = {
    'nectar': import_nectar_tentants,
    'rds': import_rds
}


class Command(BaseCommand):
    help = 'Ingest data from a csv file and put them into the database'

    def add_arguments(self, parser):
        parser.add_argument('file_name')

        parser.add_argument('-t', '--type',
                            default='nectar',
                            choices=['nectar', 'rds'],
                            help='Type of ingestion')

    def handle(self, *args, **options):
        if not os.path.exists(options['file_name']):
            raise CommandError('File "%s" does not exist' % options['file_name'])

        logger.debug('About to load the data in "%s" into the database as %s', options['file_name'], options['type'])

        # This is nectar type:
        try:
            importers[options['type']](options, self.stdout, self.stderr)

        except Exception as err:
            self.stderr.write(str(err))
