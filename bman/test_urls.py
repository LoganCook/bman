"""
Unit tests for reverse URL lookups.
"""

import unittest

from django.core.urlresolvers import resolve, reverse

#python manage.py test bman.test_urls
#python manage.py test bman.test_urls.UrlTestCase.A_Test

class UrlTestCase(unittest.TestCase):
    kwargs_noid = {'target': 'rubbish'}
    kwargs_withid = {'target': 'rubbish', 'id': 1}
    kwargs_with_method = {'target': 'rubbish', 'id': 1, 'method': 'test'}

    url_noid = '/rubbish/'
    url_withid = '/rubbish/1/'
    url_with_method = '/rubbish/1/test/'

    def test_reverse_forms(self):
        url = reverse('creation-forms', kwargs=self.kwargs_noid)
        self.assertEqual(url, '/forms' + self.url_noid)

        url = reverse('update-forms', kwargs=self.kwargs_withid)
        self.assertEqual(url, '/forms' + self.url_withid)

    def test_resolve_forms(self):
        resolved = resolve('/forms' + self.url_noid)
        self.assertEqual(resolved.view_name, 'creation-forms')

        resolved = resolve('/forms' + self.url_withid)
        self.assertEqual(resolved.view_name, 'update-forms')

    def test_reverse_objects(self):
        url = reverse('objects', kwargs=self.kwargs_noid)
        self.assertEqual(url, '/objects' + self.url_noid)

        url = reverse('object', kwargs=self.kwargs_withid)
        self.assertEqual(url, '/objects' + self.url_withid)

    def test_resolve_objects(self):
        resolved = resolve('/objects' + self.url_noid)
        self.assertEqual(resolved.view_name, 'objects')

        resolved = resolve('/objects' + self.url_withid)
        self.assertEqual(resolved.view_name, 'object')

        resolved = resolve('/objects/rubbish/stringid/')
        self.assertEqual(resolved.view_name, 'object')

    def test_resolve_api(self):
        resolved = resolve('/api' + self.url_noid)
        self.assertEqual(resolved.view_name, 'api-objects')

        resolved = resolve('/api' + self.url_withid)
        self.assertEqual(resolved.view_name, 'api-object')

        resolved = resolve('/api' + self.url_with_method)
        self.assertEqual(resolved.view_name, 'api-object-method')

        resolved = resolve('/api' + self.url_with_method)
        self.assertEqual(resolved.view_name, 'api-object-method')

    def test_reverse_api(self):
        url = reverse('api-objects', kwargs=self.kwargs_noid)
        self.assertEqual(url, '/api' + self.url_noid)

        url = reverse('api-object', kwargs=self.kwargs_withid)
        self.assertEqual(url, '/api' + self.url_withid)

        url = reverse('api-object-method', kwargs=self.kwargs_with_method)
        self.assertEqual(url, '/api' + self.url_with_method)
