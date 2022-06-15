# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_adminusers.py

# Importacion de librerias necesarias
import unittest
import logging
from http import HTTPStatus

# Importacion del archivo principal
import auth_server
from tests import aux_functions


class AdminusersTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
        app.logger.setLevel(logging.ERROR)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        print("Starting testing path \"/adminusers\" of the auth server...")
        # Creamos los usuarios a ser utilizados durante los tests
        aux_functions.createAdminTestUser("testunitadminuser_get", cls)
        aux_functions.createAdminTestUser("testunitadminuser_get_closed", cls)
        aux_functions.createAdminTestUser("testunitadminuser_post_bad_request",
                                          cls)
        aux_functions.createAdminTestUser("testunitadminuser_put", cls)
        aux_functions.createAdminTestUser("testunitadminuser_put_bad_request",
                                          cls)
        aux_functions.createAdminTestUser("testunitadminuser_patch", cls)
        aux_functions.createAdminTestUser("testunitadminuser_patch_" +
                                          "bad_request",
                                          cls)
        aux_functions.createAdminTestUser("testunitadminuser_delete", cls)
        # Creamos las sessions a ser utilizadas durante los tests
        aux_functions.createSessionAdmin("testunitadminuser_get", cls)
        aux_functions.createSessionAdmin("testunitadminuser_get", cls)
        aux_functions.createSessionAdmin("testunitadminuser_get", cls)
        aux_functions.createSessionAdmin("testunitadminuser_get", cls)
        aux_functions.createSessionAdmin("testunitadminuser_get", cls)
        # Cerramos la cuenta del usuario con cuenta cerrada
        aux_functions.closeAccountAdminTestUser("testunitadminuser_get_closed",
                                                cls)

    @classmethod
    def tearDownClass(cls):
        # Borramos los usuarios generados para los tests
        aux_functions.deleteAdminTestUser("testunitadminuser_get")
        aux_functions.deleteAdminTestUser("testunitadminuser_get_closed")
        aux_functions.deleteAdminTestUser("testunitadminuser_post")
        aux_functions.deleteAdminTestUser("testunitadminuser_post_bad_request")
        aux_functions.deleteAdminTestUser("testunitadminuser_put")
        aux_functions.deleteAdminTestUser("testunitadminuser_put_bad_request")
        aux_functions.deleteAdminTestUser("testunitadminuser_patch")
        aux_functions.deleteAdminTestUser("testunitadminuser_patch_" +
                                          "bad_request")
        aux_functions.deleteAdminTestUser("testunitadminuser_delete")
        print("Finished testing path \"/adminusers\" of the auth server!")

    def test_private_endpoints_no_api_key_should_return_unauthorized(self):
        res = self.app.get('/api/v1/adminusers')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.post('/api/v1/adminusers')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.get('/api/v1/adminusers/testunitadminuser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.put('/api/v1/adminusers/testunitadminuser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.patch('/api/v1/adminusers/testunitadminuser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.delete('/api/v1/adminusers/testunitadminuser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.get('/api/v1/adminusers/testunitadminuser/sessions')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)

    def test_post_valid_adminuser_should_return_created(self):
        r = self.app.post('/api/v1/adminusers',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunitadminuser_post",
                              password="password",
                              first_name="test",
                              last_name="test",
                              email="test@mail.com"
                              )
                          )
        self.assertEqual(HTTPStatus.CREATED, r.status_code)
        self.assertEqual("testunitadminuser_post", r.json["username"])

    def test_post_adminuser_without_username_should_return_bad_request(self):
        r = self.app.post('/api/v1/adminusers',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              password="password",
                              first_name="test",
                              last_name="test",
                              email="test@mail.com"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_post_existing_adminuser_should_return_bad_request(self):
        r = self.app.post('/api/v1/adminusers',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunitadminuser_post_bad_request",
                              password="password",
                              first_name="test",
                              last_name="test",
                              email="test@mail.com"
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_get_all_adminusers_should_return_ok(self):
        r = self.app.get('/api/v1/adminusers',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_adminusers_closed_should_return_ok(self):
        r = self.app.get('/api/v1/adminusers?show_closed=true',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_adminusers_paging_should_return_ok(self):
        r = self.app.get('/api/v1/adminusers?start=0&limit=1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_adminusers_paging_invalid_should_return_ok(self):
        r = self.app.get('/api/v1/adminusers?start=-1&limit=-1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_adminusers_paging_invalid_should_return_bad_request(self):
        r = self.app.get('/api/v1/adminusers?start=a&limit=b',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_non_existing_adminuser_should_return_not_found(self):
        r = self.app.get('/api/v1/adminusers/testunitadminuser_get_not_found',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_existing_adminuser_should_return_ok(self):
        r = self.app.get('/api/v1/adminusers/testunitadminuser_get',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual("testunitadminuser_get", r.json["username"])

    def test_put_adminuser_without_first_name_should_return_bad_request(self):
        r = self.app.put('/api/v1/adminusers/' +
                         'testunitadminuser_put_bad_request',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                             last_name="test",
                             email="test@mail.com"
                             )
                         )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_put_adminuser_should_return_ok(self):
        r = self.app.put('/api/v1/adminusers/testunitadminuser_put',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                             first_name="test",
                             last_name="test",
                             email="test@mail.com"
                             )
                         )
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual("testunitadminuser_put", r.json["username"])

    def test_put_not_existing_adminuser_should_return_not_found(self):
        r = self.app.put('/api/v1/adminusers/testunitadminuser_put_not_found',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                             first_name="test",
                             last_name="test",
                             email="test@mail.com"
                             )
                         )
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_patch_adminuser_should_return_not_found(self):
        r = self.app.patch('/api/v1/adminusers/' +
                           'testunitadminuser_patch_not_found',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/password",
                               value="test"
                               )
                           )
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_patch_adminuser_should_return_bad_request(self):
        r = self.app.patch('/api/v1/adminusers/' +
                           'testunitadminuser_patch_bad_request',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="rep",
                               path="/password",
                               value="test"
                               )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_patch_adminuser_should_return_ok(self):
        r = self.app.patch('/api/v1/adminusers/testunitadminuser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/password",
                               value="test"
                               )
                           )
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(0, r.json["code"])

    def test_delete_not_existing_adminuser_should_return_not_found(self):
        r = self.app.delete('/api/v1/adminusers/' +
                            'testunitadminuser_delete_not_found',
                            headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_delete_existing_adminuser_should_return_ok(self):
        r = self.app.delete('/api/v1/adminusers/testunitadminuser_delete',
                            headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(0, r.json["code"])

    def test_get_adminuser_sessions_should_return_ok(self):
        r = self.app.get('/api/v1/adminusers/testunitadminuser_get/sessions',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_adminuser_sessions_should_return_bad_request(self):
        r = self.app.get('/api/v1/adminusers/' +
                         'testunitadminuser_get_closed/sessions',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_adminuser_sessions_should_return_not_found(self):
        r = self.app.get('/api/v1/adminusers/' +
                         'testunitadminuser_not_found/sessions',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_delete_closed_adminuser_should_return_bad_request(self):
        r = self.app.delete('/api/v1/adminusers/' +
                            'testunitadminuser_get_closed',
                            headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_put_closed_adminuser_should_return_bad_request(self):
        r = self.app.put('/api/v1/adminusers/' +
                         'testunitadminuser_get_closed',
                         headers={'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                              first_name="test",
                              last_name="test",
                              email="test@mail.com"
                              )
                         )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_patch_closed_adminuser_should_return_bad_request(self):
        r = self.app.patch('/api/v1/adminusers/' +
                           'testunitadminuser_get_closed',
                           headers={'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                                   op="replace",
                                   path="/password",
                                   value="test"
                                   )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_get_adminuser_sessions_paging_should_return_ok(self):
        r = self.app.get('/api/v1/adminusers/testunitadminuser_get/sessions' +
                         '?start=0&limit=1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_adminuser_sessions_paging_invalid_should_return_ok(self):
        r = self.app.get('/api/v1/adminusers/testunitadminuser_get/sessions' +
                         '?start=-1&limit=-1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_adminuser_sessions_paging_inv_should_return_bad_request(self):
        r = self.app.get('/api/v1/adminusers/testunitadminuser_get/sessions' +
                         '?start=a&limit=b',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])


if __name__ == '__main__':
    unittest.main()
