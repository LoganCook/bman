# import json

import unittest
from unittest.mock import patch, mock_open

from bman.management.importers import NectarTenantImporter

TEST_DATA_FILE = 'some.csv'


class NectarTenantTestCase(unittest.TestCase):
    def setUp(self):
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.dummy = NectarTenantImporter(TEST_DATA_FILE)
            self.assertEqual(open("path/to/open").read(), "data")
            mock_file.assert_called_with("path/to/open")

    def _key_is_value(self, obj):
        self.assertIsInstance(obj, dict)
        for (k, v) in obj.items():
            self.assertEqual(k, v)

    def test_raise_runtime_error_with_invalid_file(self):
        with self.assertRaises(Exception) as cm:
            NectarTenantImporter(TEST_DATA_FILE)
        self.assertIsInstance(cm.exception, RuntimeError)

    def test_read_empty_row(self):
        with self.assertRaises(ValueError):
            self.dummy.read_row([''] * 10)

    def test_read_project_with_full_tenant_fields(self):
        # allocation_id is omitted if it is not a number
        values = self.dummy.PROJECT_FIELDS.copy()
        assert values[1] == 'allocation_id'
        values[1] = '100'
        project, managers = self.dummy.read_row(values)
        self.assertEqual(len(project), 4)
        self.assertEqual(len(managers), 0)
        self.assertIsInstance(managers, list)
        self.assertIsInstance(project['allocation_id'], int)
        del project['allocation_id']
        self._key_is_value(project)

    def test_read_project_with_managers(self):
        # allocation_id is omitted if it is not a number
        for count in range(5):
            values = self.dummy.PROJECT_FIELDS.copy()
            for _ in range(count):
                values.extend(self.dummy.MANAGER_FIELDS)
            project, managers = self.dummy.read_row(values)
            self.assertEqual(len(project), 3)
            self._key_is_value(project)
            self.assertIsInstance(managers, list)
            self.assertEqual(len(managers), count)
            for manager in managers:
                self.assertEqual(len(manager), self.dummy.MANAGER_BLOCK_SIZE)
                self._key_is_value(manager)
