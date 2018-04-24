# python manage.py test record.test_ingest_conf --settings=runner.record
import unittest
import json

from record.management.ingesters.base import UsageConfiguration


class TestConf(unittest.TestCase):
    def setUp(self):
        with open('record/config.json.example', 'r') as jf:
            self.conf_dict = json.load(jf)['Prefix of ingester class name, e.g. Tangocloudvm']['USAGE']

    def test_validation(self):
        # config.json.example has both fee-field and composition which is not allowed
        with self.assertRaises(KeyError):
            UsageConfiguration('demo', self.conf_dict)

        conf_dict_copy = self.conf_dict.copy()
        # Make it a proper configuration with only fee-field
        del conf_dict_copy['composition']
        # Make it missing orderline
        del conf_dict_copy['orderline']
        with self.assertRaises(KeyError):
            UsageConfiguration('demo', conf_dict_copy)

    def test_keys(self):
        """Test if record/config.json.example has all required fields"""
        conf_dict_copy = self.conf_dict.copy()
        # Make it a proper configuration with only fee-field
        del conf_dict_copy['composition']

        usage_conf = UsageConfiguration('demo', conf_dict_copy)
        self.assertIsNotNone(usage_conf.url)
        self.assertIsNotNone(usage_conf.headers)
        self.assertIsNotNone(usage_conf.fields)
        self.assertIsNotNone(usage_conf.fee_field)
        self.assertIsNotNone(usage_conf.orderline_linker)
        self.assertIsNotNone(usage_conf.orderline_configuration_map)
        self.assertFalse(usage_conf.is_for_composed_product)

    def test_fee_field(self):
        conf_dict_copy = self.conf_dict.copy()
        # Make it a proper configuration with only fee-field
        del conf_dict_copy['composition']

        usage_conf_with_fee_field = UsageConfiguration('demo', conf_dict_copy)
        self.assertEqual('disk', usage_conf_with_fee_field.fee_field)
        self.assertFalse(usage_conf_with_fee_field.is_for_composed_product)

        # Make it has no fee-field
        del conf_dict_copy['fee-field']
        with self.assertRaises(KeyError):
            UsageConfiguration('demo', conf_dict_copy)

    def test_composition_optional(self):
        conf_dict_copy = self.conf_dict.copy()
        # Make it a proper configuration with only composition
        del conf_dict_copy['fee-field']

        usage_conf_with_composition = UsageConfiguration('demo', conf_dict_copy)
        self.assertTrue(usage_conf_with_composition.is_for_composed_product)
        self.assertGreater(len(usage_conf_with_composition.composition_map), 0)

        # Make it has no composition
        del conf_dict_copy['composition']
        with self.assertRaises(KeyError):
            UsageConfiguration('demo', conf_dict_copy)

    def test_complex_identifier(self):
        conf_dict_copy = self.conf_dict.copy()
        # Make it a proper configuration with only composition
        del conf_dict_copy['composition']
        usage_conf = UsageConfiguration('demo', conf_dict_copy)
        self.assertTrue(usage_conf.has_aggregators)
        names = usage_conf.orderline_identifier_list
        self.assertEqual(3, len(names))
        self.assertEqual('id', names[0])
        self.assertEqual('usage1', names[1])
        self.assertEqual('usage2', names[2])

    def test_create_orderline_identifer_simple(self):
        conf_dict_copy = self.conf_dict.copy()
        # Make it a proper configuration with only composition
        del conf_dict_copy['composition']
        del conf_dict_copy['orderline']['aggregators']
        usage_conf = UsageConfiguration('demo', conf_dict_copy)

        usage_data = {'usage2': '2', 'usage1': '1', 'other': '0', 'id': 'idFirst'}
        identifer = usage_conf.create_orderline_identifer(usage_data)
        self.assertEqual('idFirst', identifer)

    def test_create_orderline_identifer_full(self):
        conf_dict_copy = self.conf_dict.copy()
        # Make it a proper configuration with only composition
        del conf_dict_copy['composition']
        usage_conf = UsageConfiguration('demo', conf_dict_copy)

        usage_data = {'usage2': '2', 'usage1': '1', 'other': '0', 'id': 'idFirst'}
        identifer = usage_conf.create_orderline_identifer(usage_data)
        self.assertEqual('idFirst,1,2', identifer)
