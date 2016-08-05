import json
from django.test import TestCase
from django.core.management import call_command

from usage.models import NovaUsage


class NovaUsageTestCase(TestCase):
    TEST_DATA_FILE = 'usage/nova_1470148200_1470320999.json'
    # Update these values when TEST_DATA_FILE has been changed
    EARLIEST = '1470148200'
    LATEST = '1470320999'
    TOTAL = 3  # records with no manager in NovaUsage will not be ingested
    CLASS_ONE_COUNT = 3
    CLASS_TWO_COUNT = 2
    CLASS_THREE_COUNT = 1

    @classmethod
    def setUpTestData(cls):
        call_command('ingest', cls.TEST_DATA_FILE, type='nova')
        with open(cls.TEST_DATA_FILE, 'r') as jf:
            cls.data = json.load(jf)

    def test_summarise_with_default(self):
        results = NovaUsage.summarise()
        self.assertEqual(len(results), self.TOTAL)
        for rslt in results:
            self.assertIn('class_one_id', rslt)

    def test_summarise_with_list_classifiers(self):
        results = NovaUsage.summarise(classifiers=['University'])
        self.assertEqual(len(results), self.CLASS_ONE_COUNT)
        for rslt in results:
            self.assertNotIn('class_one_id', rslt)
            self.assertIn('class_two_id', rslt)

        results = NovaUsage.summarise(classifiers=['University', 'School'])
        self.assertEqual(len(results), self.CLASS_TWO_COUNT)
        for rslt in results:
            self.assertNotIn('class_one_id', rslt)
            self.assertNotIn('class_two_id', rslt)
            self.assertIn('class_three_id', rslt)

        results = NovaUsage.summarise(classifiers=['University', 'School', 'Group'])
        self.assertEqual(len(results), self.CLASS_THREE_COUNT)
        for rslt in results:
            self.assertNotIn('class_one_id', rslt)
            self.assertNotIn('class_two_id', rslt)
            self.assertNotIn('class_three_id', rslt)

    def test_summarise_with_string_classifiers(self):
        results = NovaUsage.summarise(classifiers='University')
        self.assertEqual(len(results), self.CLASS_ONE_COUNT)

        results = NovaUsage.summarise(classifiers='University;School')
        self.assertEqual(len(results), self.CLASS_TWO_COUNT)

        results = NovaUsage.summarise(classifiers='University;School;Group')
        self.assertEqual(len(results), self.CLASS_THREE_COUNT)

    def test_summarise_with_ts(self):
        results = NovaUsage.summarise(start=self.EARLIEST)
        self.assertEqual(len(results), self.TOTAL)

        results = NovaUsage.summarise(end=self.LATEST)
        self.assertEqual(len(results), self.TOTAL)

        results = NovaUsage.summarise(start=self.EARLIEST, end=self.LATEST)
        self.assertEqual(len(results), self.TOTAL)
