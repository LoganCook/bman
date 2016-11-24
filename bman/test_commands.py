import unittest
from unittest.mock import patch, Mock

import django.core
import django.test
from django.core.management import call_command

TEST_DATA_FILE = 'some.csv'


class CommandTest(unittest.TestCase):
    """General tests"""
    def test_bad_choice(self):
        """Test bad type parameter"""
        with self.assertRaises(django.core.management.base.CommandError) as cm:
            call_command('ingest', 'any file', '-tNotExists')
        self.assertIn('argument -t/--type: invalid choice:', str(cm.exception))

    def test_bad_path(self):
        """Test bad path"""
        with self.assertRaises(django.core.management.base.CommandError) as cm:
            call_command('ingest', 'TEST_DATA_FILE', type='nova')
        self.assertIn('does not exist', str(cm.exception))

    def test_type_handlers_defined(self):
        import os.path
        with patch.object(os.path, 'exists', return_value=True):
            mock = Mock()
            with patch.dict('bman.management.commands.ingest.importers', {'to_be_defined': mock}):
                call_command('ingest', 'TEST_DATA_FILE', type='to_be_defined')
                self.assertTrue(mock.called)
