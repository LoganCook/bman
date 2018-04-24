# python manage.py test record.test_management_contract_helper --settings=runner.record
from django.test import TestCase

from record.management.utils.contract_helper import sort_composed_identifers, build_complex_identifer


class ContractHelperTestCase(TestCase):
    def test_sort_composed_identifers(self):
        crm_linker_name = "main"

        sorted_case1 = sort_composed_identifers(crm_linker_name)
        self.assertEqual(1, len(sorted_case1))
        self.assertEqual("main", sorted_case1[0])

        sorted_case2 = sort_composed_identifers(crm_linker_name, ("extra1", ))
        self.assertEqual(2, len(sorted_case2))
        self.assertEqual("main", sorted_case2[0])
        self.assertEqual("extra1", sorted_case2[1])

        sorted_case3 = sort_composed_identifers(crm_linker_name, ("extra1", "random2", "extra2"))
        self.assertEqual(4, len(sorted_case3))
        self.assertEqual("main", sorted_case3[0])
        self.assertEqual("extra1", sorted_case3[1])
        self.assertEqual("extra2", sorted_case3[2])
        self.assertEqual("random2", sorted_case3[3])

    def test_build_complex_identifer(self):
        usage_dict = {
            'random': 'random',
            'key2': 'value2',
            'key1': 'value1'}
        identifier = build_complex_identifer(
            sort_composed_identifers('key2', ('random', 'key1')),
            usage_dict)
        self.assertEqual(len(usage_dict), len(identifier.split(',')))
        self.assertEqual('value2,value1,random', identifier)
