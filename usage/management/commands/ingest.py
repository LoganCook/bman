"""
Ingest usage json created by reporting-unified.usage
"""

import os
import re
import json
import logging


from django.core.management.base import BaseCommand, CommandError

from usage.management import LOG_FORMAT, SAN_MS_DATE
from usage.management.importers import Importer
import usage.models

# file name contains start and end timestamps
FILE_NAME = re.compile(r'.+_(\d{10,})_(\d{10,})\.json$')

logger = logging.getLogger('usage.management')

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=SAN_MS_DATE))
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)

# fields needs to be imported for every supported services
FIELDS = {
    'Hpc': ['queue', 'owner', 'job_id', 'cores', 'cpu_seconds'],
    'Nova': ['server', 'instance_id', 'tenant', 'account',
             'span', 'image', 'flavor', 'hypervisor']
}
# Unique field for checking if exists for every supported services
UNIQUES = {'Hpc': 'job_id', 'Nova': 'instance_id'}


class Command(BaseCommand):
    help = 'Ingest data from a JSON file and put them into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_name',
            help='File path in patten of description_starttimestamp_endtimestamp.json')

        parser.add_argument('-t', '--type',
                            default='nova',
                            choices=['nova', 'hpc'],
                            help='Type of ingestion')

    def handle(self, *args, **options):
        if not os.path.exists(options['file_name']):
            raise CommandError('File "%s" does not exist' % options['file_name'])

        name_test = FILE_NAME.match(options['file_name'])
        if not name_test:
            raise CommandError('File "%s" does not meet patten request\n\tReference help.' % options['file_name'])

        timestamps = [int(ts) for ts in name_test.groups()]
        if timestamps[0] >= timestamps[1]:
            raise CommandError('File "%s" does not meet patten request\n\tReference help.' % options['file_name'])

        service = options['type'].capitalize()
        msg = 'About to ingest the data in "%s" into the database as %s usage' % (options['file_name'], service)
        logger.debug(msg)
        self.stdout.write(msg)

        try:
            manager = getattr(usage.models, service + 'Usage').objects
            with open(options['file_name'], 'r') as jf:
                importer = Importer(timestamps[0], timestamps[1], json.load(jf), manager, FIELDS[service], UNIQUES[service])
                importer.insert()
            msg = 'Ingestion completed successfully'
            logger.debug(msg)
            self.stdout.write(msg)

        except Exception as err:
            self.stderr.write(str(err))
            logger.exception('Ingestion failed')
