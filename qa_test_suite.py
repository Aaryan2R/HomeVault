import unittest
import os
import tempfile
from app import app
import database

class HomeVaultQATestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        database.DB_PATH = self.db_path
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

        # Initialize the database schema
        database.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_01_first_user_admin_registration(self):
        # Test registering the first user (should become admin)
        res = self.app.post('/register', data=dict(
            username='admin_test',
            password='password123',
            confirm='password123'
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'admin_test', res.data)
        
    def test_02_login_and_logout(self):
        self.app.post('/register', data=dict(username='test1', password='pw1', confirm='pw1'))
        # Logout
        res = self.app.post('/logout', follow_redirects=True)
        self.assertIn(b'Login', res.data)
        # Login again
        res = self.app.post('/login', data=dict(username='test1', password='pw1'), follow_redirects=True)
        self.assertIn(b'test1', res.data)

    def test_03_unauthorized_access_protection(self):
        # Trying to access download without login should redirect
        res = self.app.get('/download/1', follow_redirects=False)
        self.assertEqual(res.status_code, 302)

    def test_04_admin_dashboard_access(self):
        self.app.post('/register', data=dict(username='admin_boss', password='pw', confirm='pw'))
        res = self.app.get('/admin/users', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Manage Users', res.data)

if __name__ == '__main__':
    print("Starting Comprehensive QA Test Suite...")
    unittest.main(verbosity=2)
