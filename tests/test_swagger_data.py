# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_swagger_data.py

# Importacion de librerias necesarias
import unittest
import logging
from http import HTTPStatus

# Importacion del archivo principal
import auth_server


class StatsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
        app.logger.setLevel(logging.ERROR)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        print("Starting testing path \"/swagger-data\" of the auth server...")

    @classmethod
    def tearDownClass(cls):
        print("Finished testing path \"/swagger-data\" of the auth server!")

    def test_swagger_data_should_return_ok(self):
        r = self.app.get('/api/v1/swagger-data')
        self.assertEqual(HTTPStatus.OK, r.status_code)


if __name__ == '__main__':
    unittest.main()
