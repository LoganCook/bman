"""
Ingest usage json created by reporting-unified.usage
"""

import sys
import logging

from django.core.management.base import BaseCommand

from ..utils.command_helper import prepare_command, setup_logger

setup_logger(__name__)
logger = logging.getLogger('record.management')


class Command(BaseCommand):
    help = 'Calculate fee on ingested usage data'

    def add_arguments(self, parser):
        parser.add_argument('-t', '--type',
                            default='tangocloudvm',
                            choices=['tangocloudvm', 'nectarvm', 'xfs', 'hcp', 'hnasvv', 'hnasfs', 'hpc'],
                            help='Type of record to be calculated, should match to class name but case insensitive')

        parser.add_argument('-s', '--start', help='Start date (%%Y%%m%%d) of the interval', required=True)
        parser.add_argument('-e', '--end', help='End date "(%%Y%%m%%d)" of the interval', required=True)
        parser.add_argument('-c', '--conf',
                            default='config.json',
                            help='Path to configuration JSON file. Default = config.json')
        parser.add_argument('--substitutes-json', help='Path to JSON file downloaded from CRM for product substitutions, optional')

    def handle(self, *args, **options):
        try:
            calculator, min_date, max_date, service_config = prepare_command(options)
        except (KeyError, Exception) as err:
            self.stderr.write(err)
            sys.exit(1)

        msg = 'About to calculate for for usage of %s between %s - %s by %s ' \
              % (service_config['product-no'], min_date, max_date, type(calculator).__name__)
        logger.debug(msg)
        self.stdout.write(msg)

        calculator.calculate_fees(min_date, max_date)
