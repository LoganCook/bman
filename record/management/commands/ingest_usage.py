"""
Ingest usage json created by reporting-unified.usage
"""

import sys
import logging

from django.core.management.base import BaseCommand

from .. import LOG_FORMAT, SAN_MS_DATE
# from record.management.importers import Importer
from ..utils import prepare_command
from . import ingesters
from .ingesters import UsageConfiguration

DAY_IN_SECS = 86399  # 24 * 60 * 60 - 1

# TODO: consolidate logging
logger = logging.getLogger('record.management')

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=SAN_MS_DATE))
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)


class Command(BaseCommand):
    help = 'Ingest data from a BMAN and usage endpoints'

    @staticmethod
    def _get_ingester(normalized_service_name):
        # normalized_service_name: prefix of an ingester class which has suffix Ingester
        return getattr(ingesters, normalized_service_name + 'Ingester')

    def add_arguments(self, parser):
        parser.add_argument('-t', '--type',
                            default='tangocloudvm',
                            choices=['tangocloudvm', 'nectarvm'],
                            help='Type of ingestion, should match to class name but case insensitive')

        parser.add_argument('-s', '--start', help='Start date (%%Y%%m%%d) of the interval', required=True)
        parser.add_argument('-e', '--end', help='End date "(%%Y%%m%%d)" of the interval', required=True)
        parser.add_argument('-c', '--conf',
                            default='config.json',
                            help='Path to configuration JSON file. Default = config.json')

    def handle(self, *args, **options):
        try:
            service, min_date, max_date, service_config = prepare_command(options)
        except Exception as err:
            self.stderr.write(err)
            sys.exit(1)

        product_no = service_config['product-no']

        try:
            ingester_class = self._get_ingester(service)
        except KeyError:
            self.stderr.write('Cannot load ingester class by its prefix %s' % service)
            sys.exit(1)

        ingester = ingester_class(UsageConfiguration(product_no, service_config['USAGE']))

        msg = 'About to ingest data between %s - %s for service %s (%s) into the database' % (min_date, max_date, service, product_no)
        logger.debug(msg)
        self.stdout.write(msg)

        ingester.ingest(min_date, max_date, True)
