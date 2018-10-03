import logging

import django

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

        # changing OS will not generate a new VM
        try:
            Tangocloudvm.objects.get_or_create(**data)
        except django.db.utils.IntegrityError as err:
            msg = str(err)
            if msg.lower().find('unique constraint') > -1:
                # this just needs an update to handle OS change
                logger.warning("UNIQUE constraint failed: tango_config=%s", data)
                config = Tangocloudvm.objects.get(orderline_id=orderline.id)
                for ori, target in self.configuration.orderline_configuration_map.items():
                    value = getattr(config, target)
                    if value != usage[ori]:
                        setattr(config, target, usage[ori])
                config.save()
            else:
                raise
