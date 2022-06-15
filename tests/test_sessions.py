# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_sessions.py

# Importacion de librerias necesarias
import unittest
import logging
import warnings
from http import HTTPStatus

# Importacion del archivo principal
import auth_server
from tests import aux_functions


class SessionsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
        app.logger.setLevel(logging.ERROR)
        app.config['TESTING'] = True
        warnings.filterwarnings(action="ignore",
                                message="unclosed",
                                category=ResourceWarning)
        cls.app = app.test_client()
        print("Starting testing path \"/sessions\" of the auth server...")
        # Creamos los usuarios a ser utilizados durante los tests
        aux_functions.createTestUser("testunituser_get", cls)
        aux_functions.createTestUser("testunituser_get_not_recovery", cls)
        aux_functions.createTestUser("testunituser_post", cls)
        aux_functions.createTestUser("testunituser_post_closed", cls)
        aux_functions.createTestUser("testunituser_post_bad_request", cls)
        aux_functions.createTestUser("testunituser_delete", cls)
        aux_functions.createTestUserService("testunituser_post_service", cls)
        aux_functions.createAdminTestUser("testunitadminuser_get", cls)
        aux_functions.createAdminTestUser("testunitadminuser_post", cls)
        # Creamos las sessions a ser utilizadas durante los tests
        aux_functions.createSession("testunituser_get", cls)
        # Cerramos la cuenta del usuario con cuenta cerrada
        aux_functions.closeAccountTestUser("testunituser_post_closed", cls)

    @classmethod
    def tearDownClass(cls):
        # Borramos los usuarios generados para los tests
        aux_functions.deleteTestUser("testunituser_get")
        aux_functions.deleteTestUser("testunituser_get_no_session")
        aux_functions.deleteTestUser("testunituser_post")
        aux_functions.deleteTestUser("testunituser_post_closed")
        aux_functions.deleteTestUser("testunituser_post_bad_request")
        aux_functions.deleteTestUser("testunituser_delete")
        aux_functions.deleteTestUser("testunituser_post_service")
        aux_functions.deleteAdminTestUser("testunitadminuser_get")
        aux_functions.deleteAdminTestUser("testunitadminuser_post")
        print("Finished testing path \"/sessions\" of the auth server!")

    def test_private_endpoints_no_api_key_should_return_unauthorized(self):
        res = self.app.get('/api/v1/sessions')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.post('/api/v1/sessions')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.get('/api/v1/sessions/fake-token')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.delete('/api/v1/sessions/fake-token')

    def test_post_valid_session_should_return_created(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post",
                              password="password"
                             )
                          )
        self.assertEqual(HTTPStatus.CREATED, r.status_code)
        self.assertEqual("testunituser_post", r.json["username"])

    def test_post_session_without_username_should_return_bad_request(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              password="password"
                             )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_post_session_without_password_should_return_bad_request(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post"
                             )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_post_session_with_token_should_return_bad_request(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post",
                              login_service_token="fake-token"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_post_session_with_password_should_return_bad_request(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_service",
                              password="password"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-4, r.json["code"])

    def test_post_session_without_token_should_return_bad_request(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_service"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-4, r.json["code"])

    def test_post_session_invalid_token_should_return_unauthorized(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_service",
                              login_service_token="eyJ0eXAiOiJKV1QiLCJhbGciO" +
                                                  "iJIUzI1NiJ9.eyJpYXQiOjE2N" +
                                                  "TUzMDMxNzcsIm5iZiI6MTY1NT" +
                                                  "MwMzE3NywianRpIjoiMDQ0NDF" +
                                                  "jYmEtYzZhNS00ZjQ1LWE5N2Yt" +
                                                  "NmNjOGMxZWFlMTA5IiwiaWRlb" +
                                                  "nRpdHkiOiJjbG91ZHN5bmNnb2" +
                                                  "QiLCJmcmVzaCI6ZmFsc2UsInR" +
                                                  "5cGUiOiJhY2Nlc3MifQ.WBA1C" +
                                                  "ACXBupn3bPHSfVQ37AuBPLyno" +
                                                  "a7c2OHG53lSLQ"
                              )
                          )
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_post_session_closed_account_should_return_bad_request(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_closed",
                              password="password"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_post_session_non_existing_user_should_return_unauthorized(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_not_found",
                              password="password"
                              )
                          )
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-4, r.json["code"])

    def test_post_session_wrong_password_should_return_unauthorized(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post",
                              password="notthepassword"
                              )
                          )
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_get_all_sessions_should_return_ok(self):
        r = self.app.get('/api/v1/sessions',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_sessions_paging_should_return_ok(self):
        r = self.app.get('/api/v1/sessions?start=0&limit=1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_sessions_paging_invalid_should_return_ok(self):
        r = self.app.get('/api/v1/sessions?start=-1&limit=-1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_session_invalid_token_user_should_return_unauthorized(self):
        r = self.app.get('/api/v1/sessions/fake-token',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_get_session_invalid_user_token_should_return_unauthorized(self):
        r = self.app.get('/api/v1/sessions/eyJ0eXAiOiJKV1QiLCJhbGciO' +
                         'iJIUzI1NiJ9.eyJpYXQiOjE2N' +
                         'TUzMDMxNzcsIm5iZiI6MTY1NT' +
                         'MwMzE3NywianRpIjoiMDQ0NDF' +
                         'jYmEtYzZhNS00ZjQ1LWE5N2Yt' +
                         'NmNjOGMxZWFlMTA5IiwiaWRlb' +
                         'nRpdHkiOiJjbG91ZHN5bmNnb2' +
                         'QiLCJmcmVzaCI6ZmFsc2UsInR' +
                         '5cGUiOiJhY2Nlc3MifQ.WBA1C' +
                         'ACXBupn3bPHSfVQ37AuBPLyno' +
                         'a7c2OHG53lSLQ',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID}
                         )
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_get_session_user_should_return_ok(self):
        r1 = aux_functions.createSession("testunituser_get", self)
        r2 = self.app.get('/api/v1/sessions/' + str(r1.json['session_token']),
                          headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r2.status_code)
        self.assertEqual(str(r1.json['session_token']),
                         r2.json["session_token"])

    def test_get_session_admin_user_should_return_ok(self):
        r1 = aux_functions.createSessionAdmin("testunitadminuser_get", self)
        r2 = self.app.get('/api/v1/sessions/' + str(r1.json['session_token']),
                          headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r2.status_code)
        self.assertEqual(str(r1.json['session_token']),
                         r2.json["session_token"])

    def test_delete_session_should_return_ok(self):
        r1 = aux_functions.createSession("testunituser_delete", self)
        r2 = self.app.delete('/api/v1/sessions/' +
                             str(r1.json['session_token']),
                             headers={'X-Client-ID':
                                      aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r2.status_code)
        self.assertEqual(0, r2.json["code"])

    def test_delete_session_non_existing_token_should_return_ok(self):
        r = self.app.delete('/api/v1/sessions/fake-token',
                            headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(0, r.json["code"])

    def test_post_service_user_should_return_unauthorized(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_service",
                              login_service_token="password"
                              )
                          )
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_post_valid_admin_user_should_return_created(self):
        r = self.app.post('/api/v1/sessions',
                          headers={'Content-Type': 'application/json',
                                   'X-Admin': True,
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunitadminuser_post",
                              password="password"
                              )
                          )
        self.assertEqual(HTTPStatus.CREATED, r.status_code)
        self.assertEqual("testunitadminuser_post", r.json["username"])


if __name__ == '__main__':
    unittest.main()
