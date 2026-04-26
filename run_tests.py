import unittest
from app import app
import os
import tempfile
import database

class HomeVaultTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    def test_login_page(self):
        rv = self.app.get('/login')
        self.assertEqual(rv.status_code, 200)

    def test_register_page(self):
        rv = self.app.get('/register')
        self.assertEqual(rv.status_code, 200)

    def test_unauthorized_dashboard(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 302) # Should redirect to login

if __name__ == '__main__':
    unittest.main()
