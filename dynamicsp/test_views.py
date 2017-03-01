"""
Unit tests for views.
"""

# python manage.py test dynamicsp.test_views --sett runner.dynamicsp


from django.test import SimpleTestCase, Client
# FIXME: need to mockup a few things before this can be real tests
class ViewTestCase(SimpleTestCase):
    def test_organisation(self):
        c = Client()
        response = c.get('/api/organisation/')
        self.assertEqual(response.status_code, 200)
        response = c.get('/api/organisation/?method=get_tops')
        self.assertEqual(response.status_code, 200)
        response = c.get('/api/organisation/uuid-susm-udss-uud/get_service/?name=nectar')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), [])
        response = c.get('/api/organisation/uuid-susm-udss-uud/get_service/')
        self.assertJSONEqual(response.content.decode('utf-8'), [])
        self.assertEqual(response.status_code, 200)
        response = c.get('/api/organisation/uuid-susm-udss-uud/get_service/?name=nectar')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), [])
