import os
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from bman.models import Role, Nectar
from bman.management.importers import NectarTenantImporter

logger = logging.getLogger('bman.management')

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)


class Command(BaseCommand):
    help = 'Ingest data from a csv file and put them into the database'

    def add_arguments(self, parser):
        parser.add_argument('file_name')

        parser.add_argument('-t', '--type',
                            default='nectar',
                            choices=['nectar'],
                            help='Type of ingestion')

    def handle(self, *args, **options):
        if not os.path.exists(options['file_name']):
            raise CommandError('File "%s" does not exist' % options['file_name'])

        logger.debug('About to load the data in "%s" into the database as %s', options['file_name'], options['type'])

        # This is nectar type:
        try:
            importer = NectarTenantImporter(options['file_name'])
            projects = importer.projects
            self.stdout.write('Read %d projects' % len(projects))

            for tenant, managers in projects:
                in_db = Nectar.objects.filter(openstack_id=tenant['openstack_id']).exists()
                if in_db:
                    self.stderr.write('%(tenant)s %(openstack_id)s alread exisits. No more action.' % tenant)
                    continue

                if len(managers) > 1:
                    self.stderr.write('Multiple managers found for %(tenant)s - only one is allowed.' % tenant)
                    continue

                try:
                    mr = Role.objects.get(email=managers[0]['email'])
                    Nectar.objects.get_or_create(contractor=mr, **tenant)
                except ObjectDoesNotExist:
                    self.stderr.write('Role of manager identified by %s is not in the system. Create it first' % managers[0]['email'])
                except Exception as err:
                    logging.exception('Cannot ingest tenant: %s because %s', str(tenant), err)

        except Exception as err:
            self.stderr.write(str(err))
