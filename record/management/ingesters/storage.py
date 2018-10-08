import math
import logging

from ...models import Storage, StorageUsage
from .base import UsageIngester

logger = logging.getLogger(__name__)

KB_TO_GB = 1048576


class BaseStorageIngester(UsageIngester):
    def get_usage_class(self):
        """Get the usage class this ingester manages"""
        return StorageUsage

    def get_usage(self, start, end):
        return StorageUsage.get(start, end)

    def _save_config(self, orderline, storage_type):
        data = {
            'orderline_id': orderline.id,
            'type': storage_type
        }

        Storage.objects.get_or_create(**data)

    def get_fee_field_value(self, usage, field_name):
        """Override base method to convert storage from GB to Blocks"""
        # Even price is in GB, actual charge is calculated in blocks: 250GB/block
        # Round around block
        return math.ceil(super().get_fee_field_value(usage, field_name) / 250) * 250


class XfsIngester(BaseStorageIngester):
    def save_config(self, orderline, usage):
        # usage is not used for storage types
        super()._save_config(orderline, 'XFS')

    def save(self, start, end, orderline, usage, calculate_fee=False):
        # convert KB - > GB, make it availabe to later use in this dict
        logger.debug('usage before save: %s', usage)
        usage['usage'] = usage['usage'] / KB_TO_GB
        logger.debug('usage after conversion before save: %s', usage)
        super().save(start, end, orderline, usage, calculate_fee)


class HnasvvIngester(BaseStorageIngester):
    def save_config(self, orderline, usage):
        # usage is not used for storage types
        super()._save_config(orderline, 'HNAS VV')

    def save(self, start, end, orderline, usage, calculate_fee=False):
        # convert MB - > GB, make it availabe to later use in this dict
        logger.debug('usage before save: %s', usage)
        usage['usage'] = usage['usage'] / 1000
        logger.debug('usage after conversion before save: %s', usage)
        super().save(start, end, orderline, usage, calculate_fee)


class HnasfsIngester(BaseStorageIngester):
    def save_config(self, orderline, usage):
        # usage is not used for storage types
        super()._save_config(orderline, 'HNAS FS')

    def save(self, start, end, orderline, usage, calculate_fee=False):
        # convert MB - > GB, make it availabe to later use in this dict
        logger.debug('usage before save: %s', usage)
        usage['live_usage'] = usage['live_usage'] / 1000
        logger.debug('usage after conversion before save: %s', usage)
        super().save(start, end, orderline, usage, calculate_fee)


class HcpIngester(BaseStorageIngester):
    def save_config(self, orderline, usage):
        # usage is not used for storage types
        super()._save_config(orderline, 'HCP')

    def save(self, start, end, orderline, usage, calculate_fee=False):
        # convert Byte - > GB, make it availabe to later use in this dict
        logger.debug('usage before save: %s', usage)
        usage['ingested_bytes'] = usage['ingested_bytes'] / 1073741824
        logger.debug('usage after conversion before save: %s', usage)
        super().save(start, end, orderline, usage, calculate_fee)
