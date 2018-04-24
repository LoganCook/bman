# python manage.py test record.test_management_account_helper --settings=runner.record
import json
from unittest.mock import patch, mock_open

from django.test import TestCase

from record.management.utils.account_helper import AccountHelper


class AccountHelperTestCase(TestCase):
    def setUp(self):
        mocked = [
            {"@odata.etag": "W/\"2554944\"",
             "name": "Centre for Environmental Risk Assessment and Remediation",
             "_parentaccountid_value": "a779d575-c162-e611-80e3-c4346bc43f98",
             "accountid": "bd79d575-c162-e611-80e3-c4346bc43f98"},
            {"@odata.etag": "W/\"7520445\"",
             "name": "Google Australia",
             "_parentaccountid_value": None,
             "accountid": "dea99ffc-7e97-e711-812c-70106fa3d971"},
            {"@odata.etag": "W/\"8868220\"",
             "name": "University of South Australia",
             "_parentaccountid_value": None,
             "accountid": "a779d575-c162-e611-80e3-c4346bc43f98"},
            {"@odata.etag": "W/\"2554943\"",
             "name": "Centre for English Language in the University of South Australia",
             "_parentaccountid_value": "a779d575-c162-e611-80e3-c4346bc43f98",
             "accountid": "bb79d575-c162-e611-80e3-c4346bc43f98"}]

        with patch('record.management.utils.account_helper.open', mock_open(read_data=json.dumps({'value': mocked})), create=True) as m:
            self.account_helper = AccountHelper('inmemory_mock')
        # Just to be sure mock worked
        m.assert_called_once_with('inmemory_mock', 'r')

    def test_get_contact_accounts_of_top(self):
        google = self.account_helper.get_contact_accounts("dea99ffc-7e97-e711-812c-70106fa3d971")
        self.assertEqual(len(google), 1)
        self.assertEqual('Google Australia', google[0]['name'])
        self.assertEqual(2, len(google[0]))
        self.assertIn('name', google[0])
        self.assertIn('dynamics_id', google[0])

    def test_get_contact_accounts_of_child(self):
        # Centre for Environmental Risk Assessment and Remediation
        units = self.account_helper.get_contact_accounts("bd79d575-c162-e611-80e3-c4346bc43f98")
        self.assertEqual(len(units), 2)
        self.assertEqual('University of South Australia', units[0]['name'])
        self.assertEqual('Centre for Environmental Risk Assessment and Remediation', units[1]['name'])

    def test_get_account_id(self):
        unisa = self.account_helper.get_account_id('University of South Australia')
        self.assertEqual({'name': 'University of South Australia',
                          'dynamics_id': 'a779d575-c162-e611-80e3-c4346bc43f98'},
                         unisa)
        self.assertEqual(2, len(unisa))
        second_level_none = self.account_helper.get_account_id('Centre for Environmental Risk Assessment and Remediation')
        self.assertIsNone(second_level_none)
