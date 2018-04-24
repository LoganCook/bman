# python manage.py test record.test_utils --settings=runner.record

from django.test import TestCase

from record.management.utils import get_hierarchy


class UtilsTestCase(TestCase):
    def test_get_hierarchy(self):
        essential_fields = ('name', 'accountid')
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

        hierarchy = get_hierarchy(mocked, '_parentaccountid_value', 'accountid')
        self.assertEqual(2, len(hierarchy.keys()))

        unisa = hierarchy['University of South Australia']
        for field in essential_fields:
            self.assertTrue(field in unisa)
        self.assertTrue('parent_id' not in unisa)

        self.assertEqual(2, len(unisa['children']))
        child = unisa['children'][0]
        for field in essential_fields:
            self.assertTrue(field in child)
        self.assertTrue('parent_id' in child)

    def test_get_hierarchy_database(self):
        essential_fields = ('name', 'id', 'dynamics_id')
        mocked = [
            {"id": 2554944,
             "name": "Centre for Environmental Risk Assessment and Remediation",
             "parent_id": 8868220,
             "dynamics_id": "bd79d575-c162-e611-80e3-c4346bc43f98"},
            {"id": 7520445,
             "name": "Google Australia",
             "parent_id": None,
             "dynamics_id": "dea99ffc-7e97-e711-812c-70106fa3d971"},
            {"id": 8868220,
             "name": "University of South Australia",
             "parent_id": None,
             "dynamics_id": "a779d575-c162-e611-80e3-c4346bc43f98"},
            {"id": 2554943,
             "name": "Centre for English Language in the University of South Australia",
             "parent_id": 8868220,
             "dynamics_id": "bb79d575-c162-e611-80e3-c4346bc43f98"}]

        hierarchy = get_hierarchy(mocked, 'parent_id', 'id')
        self.assertEqual(2, len(hierarchy.keys()))

        unisa = hierarchy['University of South Australia']
        for field in essential_fields:
            self.assertTrue(field in unisa)
        self.assertTrue('parent_id' not in unisa)

        self.assertEqual(2, len(unisa['children']))
        child = unisa['children'][0]
        for field in essential_fields:
            self.assertTrue(field in child)
        self.assertTrue('parent_id' in child)
