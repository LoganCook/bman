import json

from utils import list_to_dict
from . import get_hierarchy


class AccountHelper(object):
    """Read a JSON file and retrun a two-level hierarchical structure

    Data is a file saved from the result of crm6.dynamics.com/api/data/v8.2/accounts?$select=name,_parentaccountid_value
    """
    def __init__(self, path):
        with open(path, 'r') as jf:
            data = json.load(jf)['value']

        # accountid to name and _parentaccountid_value lookup
        self.id_to_account = list_to_dict(data, 'accountid')
        self.helper = get_hierarchy(data, '_parentaccountid_value', 'accountid')

    @staticmethod
    def _extract_fields(entity):
        return {'name': entity['name'], 'dynamics_id': entity['accountid']}

    def get_accounts(self, linked_account_names):
        """Find two accounts: parent and child by their names

        The return structure can be used to create record.Account instance
        """
        # FIXME: it cannot handle admin is not in the same organization: "orderID": "FUSA0159"
        # managerUnit is from eRSA, biller is Flinders

        assert len(linked_account_names) == 2

        accounts = []
        parent = self.helper[linked_account_names[0]]
        for child in parent['children']:
            if linked_account_names[1] == child['name']:
                accounts.append(self._extract_fields(parent))
                essentials = self._extract_fields(child)
                essentials['parent_id'] = parent['accountid']
                accounts.append(essentials)
        if len(accounts) != 2:
            raise NameError("Cannot find linked account instances by their names: %s (parent) - %s (child)" % linked_account_names)
        return accounts

    def get_contact_accounts(self, accountid):
        """Get account(s) information which will be used to create Accounts"""
        # from top to bottom because some just has one top level
        if accountid in self.id_to_account:
            direct_account = self.id_to_account[accountid]
            if direct_account['_parentaccountid_value'] is not None:
                accounts = (self.id_to_account[direct_account['_parentaccountid_value']],
                            direct_account)
            else:
                accounts = (direct_account, )
            return [self._extract_fields(account) for account in accounts]
        raise KeyError('Cannot find account by its ID: %s' % accountid)

    def get_account_id(self, name):
        """Get top account's ID by its name"""
        # As there is no guarantee that there is no conflict between second level account
        # only top level account can be searched
        if name in self.helper:
            return self._extract_fields(self.helper[name])
        return None
