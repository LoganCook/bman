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

    def save_config(self, orderline, usage):
        data = {'orderline_id': orderline.id}
        try:
            for ori, target in self.configuration.orderline_configuration_map.items():
                data[target] = usage[ori]
        except KeyError as err:
            raise KeyError('Missing key %s in %s' % (err, usage))

        Tangocloudvm.objects.get_or_create(**data)
