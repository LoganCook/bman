import math
import logging

from ...models import HpcUsage
from .base import UsageIngester

logger = logging.getLogger(__name__)


class HpcIngester(UsageIngester):
    def get_usage_class(self):
        """Get the usage class this ingester manages"""
        return HpcUsage

    def get_usage(self, start, end):
        return HpcUsage.get(start, end)

    def save_config(self, orderline, usage):
        # HPC does not have any configuration
        pass
