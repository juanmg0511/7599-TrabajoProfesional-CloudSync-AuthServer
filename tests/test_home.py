# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_home.py

# Importacion de librerias necesarias
import unittest
import logging
from http import HTTPStatus

# Importacion del archivo principal
import auth_server


class HomeTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
        app.logger.setLevel(logging.ERROR)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        print("Starting testing path \"/\" of the auth server...")

    @classmethod
    def tearDownClass(cls):
        print("Finished testing path \"/\" of the auth server!")

    def test_home_should_return_ok(self):
        r = self.app.get('/')
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertTrue('7599-cloudsync-auth-server-v1.00' in
                        r.get_data(as_text=True))

    def test_status_should_return_ok(self):
        r = self.app.get('/status')
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual('online', r.json['data']['server_status'])
        self.assertEqual('online', r.json['data']['app_database_status'])
        self.assertEqual('online', r.json['data']['log_database_status'])

    def test_on_starting_should_return_ok(self):
        auth_server.on_starting(None)


if __name__ == '__main__':
    unittest.main()
