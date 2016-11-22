import unittest
from unittest.mock import patch

import django.core
import django.test
from django.core.management import call_command
from django.utils.six import StringIO

from usage.management.importers import Importer

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

    def test_importer_constructor(self):
        with patch('usage.management.commands.ingest.Importer') as MockClass:
            call_command('ingest', TEST_DATA_FILE, type=self.test_type)
            args, _ = MockClass.call_args
            self.assertEqual(len(args), 6)
            self.assertIsInstance(args[0], int)
            self.assertIsInstance(args[1], int)
            self.assertIsInstance(args[2], list)
            self.assertIsInstance(args[3], object)
            self.assertIsInstance(args[4], list)
            self.assertIsInstance(args[5], str)
