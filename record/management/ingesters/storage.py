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

    def calculate_fee(self, usage, start, end):
        """Override base method to calculate fee for storage"""
        logger.debug('usage sent to calculate_fee: %s', usage.usage)
        # Even price is in GB, actual charge is calculated in blocks: 250GB
        # Round around block
        used_space = math.ceil(getattr(usage, self.configuration.fee_field) / 250) * 250
        logger.debug('used_space: %s', used_space)
        # FIXME: change from do everything in derived class to just modify usage fields
        # then call super().calculated_fee with updated usage fields
        return used_space * self._get_price(usage.orderline.order.price_list, start, end)


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
        super()._save_config(orderline, 'HNAS Virtual Volume')

    def save(self, start, end, orderline, usage, calculate_fee=False):
        # convert MB - > GB, make it availabe to later use in this dict
        logger.debug('usage before save: %s', usage)
        usage['usage'] = usage['usage'] / 1000
        logger.debug('usage after conversion before save: %s', usage)
        super().save(start, end, orderline, usage, calculate_fee)


class HnasfsIngester(BaseStorageIngester):
    def save_config(self, orderline, usage):
        # usage is not used for storage types
        super()._save_config(orderline, 'HNAS File System')

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
