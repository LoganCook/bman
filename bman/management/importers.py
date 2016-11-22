import csv
import logging

logger = logging.getLogger(__name__)
NO_DATA = "No data"  # used in raising ValueError when empty row is seen


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
    PROJECT_BLOCK_SIZE = len(PROJECT_FIELDS)
    MANAGER_FIELDS = ['openstack_id', 'name', 'email', 'domain']
    MANAGER_BLOCK_SIZE = len(MANAGER_FIELDS)

    def __init__(self, fn):
        self.projects = []
        try:
            with open(fn, 'r') as csvfile:
                spamreader = csv.reader(csvfile)
                for row in spamreader:
                    try:
                        self.projects.append(self.read_row(row))
                    except ValueError as err:
                        if str(err) != NO_DATA:
                            raise err
                    except Exception as err:
                        raise RuntimeError("fail to read line %s. Error: %s" % (row, str(err)))
        except Exception as err:
            raise RuntimeError("Cannot process csv file %s: %s" % (fn, str(err)))

    def read_row(self, row):
        """Reads a row in blocks and create project and manager objects

        In row, first block is project, second has one to many manager block
        Returns a tuple: project object, a list of manager objects
        """
        pos = 0
        count = len(row)

        current = []
        for pos in range(self.PROJECT_BLOCK_SIZE):
            current.append(row[pos].strip())
        if "".join(current) == "":
            raise ValueError(NO_DATA)
        tenant = dict(zip(self.PROJECT_FIELDS, current))
        try:
            tenant['allocation_id'] = int(tenant['allocation_id'])
        except ValueError:
            del tenant['allocation_id']

        managers = []
        while pos < count - 1:
            current = []
            block_start = pos + 1
            for pos in range(block_start, block_start + self.MANAGER_BLOCK_SIZE):
                current.append(row[pos].strip())
            if "".join(current):
                managers.append(dict(zip(self.MANAGER_FIELDS, current)))

        if len(managers) > 1:
            logger.debug('%s with %d managers:', tenant['tenant'], len(managers))
            logger.debug(managers)
        return (tenant, managers)


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    projects = NectarTenantImporter('../sa_unis_tenants.csv')
    logger.debug("Read %d projects", len(projects.projects))
