import json

from utils import list_to_dict


def create_flavor_dict(path):
    with open(path, 'r') as jf:
        return list_to_dict(json.load(jf),
                            'openstack_id', ('vcpus', 'ephemeral', 'disk', 'name', 'ram'))
