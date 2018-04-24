"""
Ingest usage json created by reporting-unified.usage
"""

import sys
import logging

from django.core.management.base import BaseCommand

from .. import LOG_FORMAT, SAN_MS_DATE
from ..utils import prepare_command
from .ingesters import UsageConfiguration, TangocloudvmIngester


# TODO: consolidate logging
logger = logging.getLogger('record.management')

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=SAN_MS_DATE))
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)


class Command(BaseCommand):
    help = 'Ingest data from a BMAN and usage endpoints'

    def add_arguments(self, parser):
        parser.add_argument('-t', '--type',
                            default='tangovm',
                            choices=['tangovm', 'hpc'],
                            help='Type of ingestion')

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

        # TODO: this need more work for calling different ingesters
        if service == 'Tangovm':
            calculator = TangocloudvmIngester(UsageConfiguration(product_no, service_config['USAGE']))

        msg = 'About to ingest data between %s - %s for service %s (%s) into the database' % (min_date, max_date, service, product_no)
        logger.debug(msg)
        self.stdout.write(msg)

        calculator.calculate_fees(min_date, max_date)
