import csv
import logging

logger = logging.getLogger(__name__)

class NectarTenantImporter(object):
    """Import tenants and their managers from a csv file

    csv file is genereated by reporting-unified/biller.export_tenants.
    It does not have titles. Each row has blocks:
    1. tenant: fields are defined in PROJECT_FIELDS
    2. managers: fields are defined in MANAGER_FIELDS. This block can apprear a few times.

    Result is in NectarTenantImporter.projects which is a list of
    two-element tuples: [0]: tenant, [1]: list of managers.
    """

    PROJECT_FIELDS = ['openstack_id', 'allocation_id', 'tenant', 'description']
    MANAGER_FIELDS = ['openstack_id', 'name', 'email', 'domain']

    def __init__(self, fn):
        self.projects = []
        try:
            with open(fn, 'r') as csvfile:
                spamreader = csv.reader(csvfile)
                for row in spamreader:
                    self.projects.append(self._read_row(row))
        except Exception as e:
            raise RuntimeError("Cannot process csv file %s: %s" % (fn, str(e)))

    def _read_row(self, row):
        pos = 0
        count = len(row)

        current = []
        for f in self.PROJECT_FIELDS:
            current.append(row[pos].strip())
            pos += 1
        tenant = dict(zip(self.PROJECT_FIELDS, current))
        try:
            tenant['allocation_id'] = int(tenant['allocation_id'])
        except:
            del tenant['allocation_id']

        managers = []
        while pos < count:
            current = []
            for f in self.MANAGER_FIELDS:
                current.append(row[pos].strip())
                pos += 1
            if "".join(current):
                managers.append(dict(zip(self.MANAGER_FIELDS, current)))

        if len(managers) > 1:
            logger.debug('%s with %d managers:' % (tenant['tenant'], len(managers)))
            logger.debug(managers)
        return (tenant, managers)


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    projects = NectarTenantImporter('adelaide.edu.au_tenants.csv')
    logger.debug("Read %d projects" % len(projects.projects))
