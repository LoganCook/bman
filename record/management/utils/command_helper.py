import os
import json
import logging

from date_helpers import date_range_to_timestamps
from .. import LOG_FORMAT, SAN_MS_DATE, ingesters
from .contract_helper import ProductSubstitute
from ..ingesters.base import UsageConfiguration

logger = logging.getLogger('record.management')
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=SAN_MS_DATE))
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)


def read_conf(path):
    """Read a configuration JSON with a structure shown in record.config.json.example"""
    # Check that the configuration file exists
    if not os.path.isfile(path):
        raise Exception('Config file %s cannot be found' % path)

    with open(path, 'r') as f:
        conf = json.load(f)
    return conf


def get_ingester_class(normalized_service_name):
    """"Get ingester class from management.ingesters package"""
    # normalized_service_name: prefix of an ingester class which has suffix Ingester
    return getattr(ingesters, normalized_service_name + 'Ingester')


def prepare_command(options):
    """Parse a command options

    to get an instance of an ingester class, man_date, max_date and config of the service
    including key product-no and CRM and USAGE objects.
    Keys checked are: start, end, conf and substitutes_json.
    """
    min_date, max_date = date_range_to_timestamps(options['start'], options['end'])

    logger.info("Config file path %s", options['conf'])
    config = read_conf(options['conf'])

    service_name = options['type'].capitalize()
    if service_name not in config:
        raise KeyError('No configuration found for %s' % service_name)

    # product substitutes
    if options['substitutes_json']:
        substitutes = ProductSubstitute()
        substitutes.load_from_file(options['substitutes_json'])
    else:
        substitutes = None

    usage_config = UsageConfiguration(config[service_name]['product-no'], config[service_name]['USAGE'])

    # get ingester class
    try:
        ingester_class = get_ingester_class(service_name)
    except KeyError:
        raise KeyError('Cannot load ingester class by its prefix %s' % service_name)

    ingester = ingester_class(usage_config, substitutes)
    return ingester, min_date, max_date, config[service_name]
