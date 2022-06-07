# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_requestlog.py

# Importacion de librerias necesarias
import unittest
import logging
from http import HTTPStatus
from datetime import datetime

# Importacion del archivo principal
import auth_server
from tests import aux_functions


class RequestLogTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
        app.logger.setLevel(logging.ERROR)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        print("Starting testing path \"/requestlog\" of the auth server...")
        # Generamos un par de requests a la api para generar estadisticas
        cls.app.get('/api/v1/users',
                    headers={'X-Client-ID': aux_functions.X_Client_ID})
        cls.app.get('/api/v1/adminusers',
                    headers={'X-Client-ID': aux_functions.X_Client_ID})

    @classmethod
    def tearDownClass(cls):
        print("Finished testing path \"/requestlog\" of the auth server!")

    def test_private_endpoints_no_api_key_should_return_unauthorized(self):
        res = self.app.get('/api/v1/requestlog?' +
                           'startdate=2022-05-01&enddate=2010-05-01')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)

    def test_requestlog_should_return_ok(self):
        today = str(datetime.utcnow().date())
        r = self.app.get('/api/v1/requestlog?startdate=' + today +
                         '&enddate=' + today,
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)

    def test_requestlog_should_return_ok_sort(self):
        today = str(datetime.utcnow().date())
        r = self.app.get('/api/v1/requestlog?startdate=' + today +
                         '&enddate=' + today + '&sortascending=True',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)

    def test_requestlog_should_return_ok_filter(self):
        today = str(datetime.utcnow().date())
        r = self.app.get('/api/v1/requestlog?startdate=' + today +
                         '&enddate=' + today +
                         '&filter={"comparator":"in","field":"status",' +
                         '"value":"200"}',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)

    def test_requestlog_should_return_bad_request(self):
        r = self.app.get('/api/v1/requestlog?' +
                         'startdate=invaliddate&enddate=2022-05-01',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json['code'])

    def test_requestlog_should_return_bad_request_2(self):
        r = self.app.get('/api/v1/requestlog?' +
                         'startdate=2022-05-01&enddate=2010-05-01',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json['code'])

    def test_requestlog_should_return_bad_request_3(self):
        r = self.app.get('/api/v1/requestlog?' +
                         'startdate=2022-05-01&enddate=2010-05-01&' +
                         'filter={"invalid_filter"}',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json['code'])


if __name__ == '__main__':
    unittest.main()
