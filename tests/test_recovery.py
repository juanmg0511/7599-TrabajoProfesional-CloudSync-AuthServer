# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_recovery.py

# Importacion de librerias necesarias
import unittest
import logging
from http import HTTPStatus

# Importacion del archivo principal
import auth_server
from tests import aux_functions


class RecoveryTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
        app.logger.setLevel(logging.ERROR)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        print("Starting testing path \"/recovery\" of the auth server...")
        # Creamos los usuarios a ser utilizados durante los tests
        aux_functions.createTestUser("testunituser_get", cls)
        aux_functions.createTestUser("testunituser_get_not_recovery", cls)
        aux_functions.createTestUser("testunituser_post", cls)
        aux_functions.createTestUser("testunituser_post_bad_request", cls)
        aux_functions.createTestUser("testunituser_post_closed", cls)
        aux_functions.createTestUserService("testunituser_post_service", cls)
        aux_functions.createTestUserService("testunituser_get_service", cls)
        # Creamos los recovery requests a ser utilizados durante los tests
        aux_functions.createRecoveryRequest("testunituser_get", cls)
        aux_functions.createRecoveryRequest("testunituser_get", cls)
        aux_functions.createRecoveryRequest("testunituser_post", cls)
        # Cerramos la cuenta del usuario con cuenta cerrada
        aux_functions.closeAccountTestUser("testunituser_post_closed", cls)

    @classmethod
    def tearDownClass(cls):
        # Borramos los usuarios generados para los tests
        aux_functions.deleteTestUser("testunituser_get")
        aux_functions.deleteTestUser("testunituser_get_not_recovery")
        aux_functions.deleteTestUser("testunituser_post")
        aux_functions.deleteTestUser("testunituser_post_bad_request")
        aux_functions.deleteTestUser("testunituser_post_closed")
        aux_functions.deleteTestUser("testunituser_post_service")
        aux_functions.deleteTestUser("testunituser_get_service")

        print("Finished testing path \"/recovery\" of the auth server!")

    def test_private_endpoints_no_api_key_should_return_unauthorized(self):
        res = self.app.get('/api/v1/recovery')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.post('/api/v1/recovery')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.get('/api/v1/recovery/testunituser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.post('/api/v1/recovery/testunituser')

    def test_post_valid_recovery_should_return_created(self):
        r = self.app.post('/api/v1/recovery',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post"
                              )
                          )
        self.assertEqual(HTTPStatus.CREATED, r.status_code)
        self.assertEqual("testunituser_post", r.json["username"])

    def test_post_recovery_without_username_should_return_bad_request(self):
        r = self.app.post('/api/v1/recovery',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_post_recovery_non_existing_user_should_return_not_found(self):
        r = self.app.post('/api/v1/recovery',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_not_found"
                              )
                          )
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_all_recovery_requests_should_return_ok(self):
        r = self.app.get('/api/v1/recovery',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_recovery_requests_paging_should_return_ok(self):
        r = self.app.get('/api/v1/recovery?start=0&limit=1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_recovery_requests_paging_invalid_should_return_ok(self):
        r = self.app.get('/api/v1/recovery?start=-1&limit=-1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_recovery_requests_pag_inv_should_return_bad_request(self):
        r = self.app.get('/api/v1/recovery?start=a&limit=b',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_recovery_non_existing_user_should_return_not_found(self):
        r = self.app.get('/api/v1/recovery/testunituser_get_not_found',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_recovery_non_recovery_user_should_return_unauthorized(self):
        r = self.app.get('/api/v1/recovery/testunituser_get_not_recovery',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_get_recovery_should_return_ok(self):
        r = self.app.get('/api/v1/recovery/testunituser_get',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual("testunituser_get", r.json["username"])

    def test_post_recovery_without_key_should_return_bad_request(self):
        r = self.app.post('/api/v1/recovery/testunituser_post_bad_request',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              new_password="test"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_post_recovery_user_wrong_key_should_return_unauthorized(self):
        r = self.app.post('/api/v1/recovery/testunituser_get',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              recovery_key="ef08e594-9912-11ea" +
                                           "-80b2-b20148589bd1",
                              new_password="test"
                              )
                          )
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_post_recovery_non_existing_user_should_return_not_found_2(self):
        r = self.app.post('/api/v1/recovery/testunituser_post_not_found',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              recovery_key="ef08e594-9912-11ea" +
                                           "-80b2-b20148589bd1",
                              new_password="test"
                              )
                          )
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_post_recovery_non_recovery_user_should_return_unauthorized(self):
        r = self.app.post('/api/v1/recovery/testunituser_post_bad_request',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              recovery_key="ef08e594-9912-11ea" +
                                           "-80b2-b20148589bd1",
                              new_password="test"
                              )
                          )
        self.assertEqual(HTTPStatus.UNAUTHORIZED, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_post_recovery_user_should_return_ok(self):
        r1 = aux_functions.createRecoveryRequest("testunituser_post", self)
        r2 = self.app.post('/api/v1/recovery/testunituser_post',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               recovery_key=r1.json["recovery_key"],
                               new_password="test"
                               )
                           )
        self.assertEqual(HTTPStatus.OK, r2.status_code)
        self.assertEqual(0, r2.json["code"])

    def test_post_closed_account_should_return_bad_request(self):
        r = self.app.post('/api/v1/recovery',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_closed"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_post_login_service_should_return_bad_request(self):
        r = self.app.post('/api/v1/recovery',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_service"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_get_closed_account_should_return_bad_request(self):
        r = self.app.get('/api/v1/recovery/testunituser_post_closed',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_login_service_should_return_bad_request(self):
        r = self.app.get('/api/v1/recovery/testunituser_get_service',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_post_user_closed_account_should_return_bad_request(self):
        r = self.app.post('/api/v1/recovery/testunituser_post_closed',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              recovery_key="a_token",
                              new_password="a_password"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_post_user_login_service_should_return_bad_request(self):
        r = self.app.post('/api/v1/recovery/testunituser_post_service',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              recovery_key="a_token",
                              new_password="a_password"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-3, r.json["code"])


if __name__ == '__main__':
    unittest.main()
