import logging

from ...models import Tangocloudvm, TangocloudvmUsage
from .base import UsageIngester

logger = logging.getLogger(__name__)


class TangocloudvmIngester(UsageIngester):
    def get_usage_class(self):
        """Get the usage class this ingester manages"""
        return TangocloudvmUsage

    def get_usage(self, start, end):
        # This usage actually comes from config table Tangocloudvm: only core and ram are used
        return Tangocloudvm.get(start, end)

    # TODO: change it to using ingesting config
    def save_config(self, orderline, usage):
        try:
            Tangocloudvm.objects.get_or_create(
                orderline=orderline,
                server_id=usage['id'],
                server=usage['server'],
                core=usage['core'],
                ram=usage['ram'],
                os=usage['os'],
                business_unit=usage['businessUnit'])
        except Exception as err:
            logger.error('Failed to record configuration of instance with id=%s, product number=%s, detail: %s',
                         usage['id'],
                         self.configuration.product_no,
                         err)
