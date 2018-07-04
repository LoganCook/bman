import logging

from ...models import Nectarvm, NectarvmUsage
from ..utils import get_json
from ..utils.flavors import create_flavor_dict
from .base import UsageIngester

logger = logging.getLogger(__name__)


class NectarvmIngester(UsageIngester):
    def __init__(self, usage_conf, substitutes):
        flavors_json_path = usage_conf.configuration.pop('flavor-json-path')
        super().__init__(usage_conf, substitutes)
        self.flavors = create_flavor_dict(flavors_json_path)

    def get_data(self, start, end):
        # Url of usage data is a json file 'usage/nova/NovaUsage_'  + startTs + '_' + endTs + '.json'
        url = '%s/NovaUsage_%d_%d.json' % (self.configuration.url, start, end)
        return get_json(url)

    def get_usage_class(self):
        """Get the usage class this ingester manages"""
        return NectarvmUsage

    def get_usage(self, start, end):
        # This usage actually comes from config table Nectarvm: only vcpu is used
        return Nectarvm.get(start, end)

    def save_config(self, orderline, usage):
        # {
        #   "server": "emuwn-default-TceQGpsO",
        #   "hypervisor": "cw-compute-05a.sa.nectar.org.au",
        #   "image": "ada2876f-e2b7-4a65-b7bf-ffaef46639b0",
        #   "manager": [],
        #   "server_id": "50f74b47-f903-46ae-bad2-8d7d6ab51b76",
        #   "span": 2673418,
        #   "account": "fe6617c5c45544a2985ed0300539d7cb",
        #   "flavor": "2",
        #   "tenant": "bfdd028c2d494dc7b0b90478e7a8232b",
        #   "az": "sa",
        #   "instance_id": "01b5eb69-cb0a-4d94-b6e5-6ec00c5f7202"
        # }
        # Update useage with flavor information, this will be available to the next caller
        data = {'orderline_id': orderline.id}
        if self.flavors[usage['flavor']] is None:
            raise ValueError('Cannot map flavor id %s' % usage['flavor'])
        usage.update(self.flavors[usage['flavor']])
        try:
            for ori, target in self.configuration.orderline_configuration_map.items():
                data[target] = usage[ori]
        except KeyError as err:
            raise KeyError('Missing key %s in %s' % (err, usage))

        Nectarvm.objects.get_or_create(**data)
