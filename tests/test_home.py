# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_home.py

# Importacion de librerias necesarias
import unittest
from http import HTTPStatus
from datetime import datetime

# Importacion del archivo principal
import auth_server


class HomeTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
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

    def test_ping_should_return_ok(self):
        r = self.app.get('/ping')
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual('Ping.', r.json['message'])

    def test_stats_should_return_ok(self):
        today = str(datetime.utcnow().date())
        r = self.app.get('/stats?startdate=' + today + '&enddate=' + today)
        self.assertEqual(HTTPStatus.OK, r.status_code)

    def test_stats_should_return_bad_request(self):
        r = self.app.get('/stats?startdate=invaliddate&enddate=2020-05-01')
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json['code'])

    def test_stats_should_return_bad_request_2(self):
        r = self.app.get('/stats?startdate=2020-05-01&enddate=2020-04-01')
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json['code'])

    def test_status_should_return_ok(self):
        r = self.app.get('/status')
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual('online', r.json['data']['server_status'])
        self.assertEqual('online', r.json['data']['database_status'])


if __name__ == '__main__':
    unittest.main()
