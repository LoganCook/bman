import json
import django.core

import unittest
from unittest.mock import patch

import django.test
from django.core.management import call_command
from django.utils.six import StringIO

from usage.management.importers import Importer, NovaUsageImporter

TEST_DATA_FILE = 'usage/nova_1470148200_1470320999.json'


class CommandTest(unittest.TestCase):
    def test_bad_type(self):
        with self.assertRaises(django.core.management.base.CommandError) as cm:
            call_command('ingest', 'any file', '-tNotExists')
        self.assertIn('argument -t/--type: invalid choice:', str(cm.exception))

    def test_bad_name_pattern(self):
        import os.path
        with patch.object(os.path, 'exists', return_value=True):
            with self.assertRaises(django.core.management.base.CommandError) as cm:
                call_command('ingest', 'any file', '-tnova')
            self.assertIn('does not meet patten request', str(cm.exception))

    def test_bad_path(self):
        with self.assertRaises(django.core.management.base.CommandError):
            call_command('ingest', 'TEST_DATA_FILE', type='nova')


class ImporterTest(unittest.TestCase):
    def setUp(self):
        self.test_type = 'nova'

    def test_importer_insert_call(self):
        out = StringIO()
        err = StringIO()
        with patch.object(Importer, 'insert') as mocked:
            call_command('ingest', TEST_DATA_FILE, type=self.test_type, stdout=out, stderr=err)
            self.assertTrue(mocked.called)
        self.assertEqual(err.getvalue(), '')
        self.assertIn('Ingestion completed successfully', out.getvalue())

    def test_derived_importer(self):
        with patch('usage.management.importers.NovaUsageImporter') as MockClass:
            call_command('ingest', TEST_DATA_FILE, type=self.test_type)
            args, _ = MockClass.call_args
            self.assertIsInstance(args[0], int)
            self.assertIsInstance(args[1], int)
            self.assertIsInstance(args[2], list)


class NovaUsageImporterTest(django.test.TestCase):
    def setUp(self):
        with open(TEST_DATA_FILE, 'r') as jf:
            self.data = json.load(jf)

    def test_can_ingest(self):
        importer = NovaUsageImporter(1470148200, 1470320999, self.data)
        importer.insert()
