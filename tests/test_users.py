# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_users.py

# Importacion de librerias necesarias
import unittest
import logging
from http import HTTPStatus

# Importacion del archivo principal
import auth_server
from src import helpers
from tests import aux_functions


class UsersTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
        app.logger.setLevel(logging.ERROR)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        print("Starting testing path \"/users\" of the auth server...")
        # Creamos los usuarios a ser utilizados durante los tests
        aux_functions.createTestUser("testunituser_get", cls)
        aux_functions.createTestUser("testunituser_get_closed", cls)
        aux_functions.createTestUser("testunituser_post_bad_request", cls)
        aux_functions.createTestUser("testunituser_put", cls)
        aux_functions.createTestUser("testunituser_put_bad_request", cls)
        aux_functions.createTestUser("testunituser_patch", cls)
        aux_functions.createTestUser("testunituser_patch_bad_request", cls)
        aux_functions.createTestUserService("testunituser_patch_service", cls)
        aux_functions.createTestUser("testunituser_delete", cls)
        # Creamos las sessions a ser utilizadas durante los tests
        aux_functions.createSession("testunituser_get", cls)
        aux_functions.createSession("testunituser_get", cls)
        aux_functions.createSession("testunituser_get", cls)
        aux_functions.createSession("testunituser_get", cls)
        aux_functions.createSession("testunituser_get", cls)
        # Cerramos la cuenta del usuario con cuenta cerrada
        aux_functions.closeAccountTestUser("testunituser_get_closed", cls)

    @classmethod
    def tearDownClass(cls):
        # Borramos los usuarios generados para los tests
        aux_functions.deleteTestUser("testunituser_get")
        aux_functions.deleteTestUser("testunituser_get_closed")
        aux_functions.deleteTestUser("testunituser_post")
        aux_functions.deleteTestUser("testunituser_post_bad_request")
        aux_functions.deleteTestUser("testunituser_put")
        aux_functions.deleteTestUser("testunituser_put_bad_request")
        aux_functions.deleteTestUser("testunituser_patch")
        aux_functions.deleteTestUser("testunituser_patch_bad_request")
        aux_functions.deleteTestUser("testunituser_patch_service")
        aux_functions.deleteTestUser("testunituser_delete")
        print("Finished testing path \"/users\" of the auth server!")

    def test_private_endpoints_no_api_key_should_return_unauthorized(self):
        res = self.app.get('/api/v1/users')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.post('/api/v1/users')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.get('/api/v1/users/testunituser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.put('/api/v1/users/testunituser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.patch('/api/v1/users/testunituser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.delete('/api/v1/users/testunituser')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)
        res = self.app.get('/api/v1/users/testunituser/sessions')
        self.assertEqual(HTTPStatus.UNAUTHORIZED, res.status_code)

    def test_post_valid_user_should_return_created(self):
        r = self.app.post('/api/v1/users',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post",
                              password="password",
                              first_name="test",
                              last_name="test",
                              contact=dict(
                                  phone="1545642323",
                                  email="testunituser_post@mail.com"
                                  ),
                              avatar=dict(
                                isUrl=True,
                                data="http://www.google.com"
                              )
                              )
                          )
        self.assertEqual(HTTPStatus.CREATED, r.status_code)
        self.assertEqual("testunituser_post", r.json["username"])

    def test_post_user_without_username_should_return_bad_request(self):
        r = self.app.post('/api/v1/users',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              password="password",
                              first_name="test",
                              last_name="test",
                              contact=dict(
                                  phone="1545642323",
                                  email="test@mail.com"
                                  )
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_post_user_invalid_email_should_return_bad_request(self):
        r = self.app.post('/api/v1/users',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_bad_request",
                              password="password",
                              first_name="test",
                              last_name="test",
                              contact=dict(
                                  phone="1545642323",
                                  email="testmail.com"
                                  )
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_post_user_invalid_avatar_should_return_bad_request(self):
        r = self.app.post('/api/v1/users',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_bad_request",
                              password="password",
                              first_name="test",
                              last_name="test",
                              contact=dict(
                                  phone="1545642323",
                                  email="testunituser_post_bad_rq@mail.com"
                                  ),
                              avatar=dict(
                                  url="testmalurl"
                                  )
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_post_existing_user_should_return_bad_request(self):
        r = self.app.post('/api/v1/users',
                          headers={'Content-Type': 'application/json',
                                   'X-Client-ID': aux_functions.X_Client_ID},
                          json=dict(
                              username="testunituser_post_bad_request",
                              password="password",
                              first_name="test",
                              last_name="test",
                              contact=dict(
                                  phone="1545642323",
                                  email="testunituser_post_bad_rq@mail.com"
                                  )
                              )
                          )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-5, r.json["code"])

    def test_get_all_users_should_return_ok(self):
        r = self.app.get('/api/v1/users',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_users_closed_should_return_ok(self):
        r = self.app.get('/api/v1/users?show_clo',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_all_users_paging_should_return_ok(self):
        r = self.app.get('/api/v1/users?start=0&limit=1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_allusers_paging_invalid_should_return_ok(self):
        r = self.app.get('/api/v1/users?start=-1&limit=-1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_allusers_paging_invalid_should_return_bad_request(self):
        r = self.app.get('/api/v1/users?start=a&limit=b',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_non_existing_user_should_return_not_found(self):
        r = self.app.get('/api/v1/users/testunituser_get_not_found',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_existing_user_should_return_ok(self):
        r = self.app.get('/api/v1/users/testunituser_get',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual("testunituser_get", r.json["username"])

    def test_put_user_without_first_name_should_return_bad_request(self):
        r = self.app.put('/api/v1/users/testunituser_put_bad_request',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                             last_name="test",
                             contact=dict(
                                 phone="1545642323",
                                 email="testunituser_put_bad_request@mail.com"
                                 )
                             )
                         )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_put_user_invalid_email_should_return_bad_request(self):
        r = self.app.put('/api/v1/users/testunituser_put_bad_request',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                             first_name="test",
                             last_name="test",
                             contact=dict(
                                 phone="1545642323",
                                 email="testmail.com"
                                 )
                             )
                         )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_put_user_invalid_avatar_should_return_bad_request(self):
        r = self.app.put('/api/v1/users/testunituser_put_bad_request',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                             first_name="test",
                             last_name="test",
                             contact=dict(
                                 phone="1545642323",
                                 email="testunituser_put_bad_request@mail.com"
                                 ),
                             avatar=dict(
                                 url="testmalurl"
                                 )
                             )
                         )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_put_user_should_return_ok(self):
        r = self.app.put('/api/v1/users/testunituser_put',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                             first_name="test",
                             last_name="test",
                             contact=dict(
                                 phone="1545642323",
                                 email="testunituser_put@mail.com"
                                 ),
                             avtar=dict(
                                isUrl=True,
                                data="http://www.google.com"
                             )
                             )
                         )
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual("testunituser_put", r.json["username"])

    def test_put_not_existing_user_should_return_not_found(self):
        r = self.app.put('/api/v1/users/testunituser_put_not_found',
                         headers={'Content-Type': 'application/json',
                                  'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                             first_name="test",
                             last_name="test",
                             contact=dict(
                                 phone="1545642323",
                                 email="testunituser_put_not_found@mail.com"
                                 )
                             )
                         )
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_patch_user_should_return_not_found(self):
        r = self.app.patch('/api/v1/users/testunituser_patch_not_found',
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

    def test_patch_user_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/testunituser_patch_bad_request',
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

    def test_patch_service_user_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/testunituser_patch_service',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/password",
                               value="test"
                               )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-4, r.json["code"])

    def test_patch_user_should_return_ok(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/password",
                               value="12345"
                               )
                           )
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(0, r.json["code"])

    def test_patch_user_avatar_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/avatar",
                               value="test"
                               )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_patch_user_avatar_url_should_return_ok(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/avatar",
                               value=dict(
                                isUrl=True,
                                data="http://www.gogle.com"
                               )
                               )
                           )
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(0, r.json["code"])

    def test_patch_user_avatar_url_invalid_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/avatar",
                               value=dict(
                                isUrl=True,
                                data="Test"
                               )
                               )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_patch_user_avatar_img_should_return_ok(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/avatar",
                               value=dict(
                                isUrl=False,
                                data="\"" +
                                     helpers.loadTextFile("tests/img/" +
                                                          "test_img_o" +
                                                          "k.txt") +
                                     "\""
                               )
                               )
                           )
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(0, r.json["code"])

    def test_patch_user_avatar_img_dim_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/avatar",
                               value=dict(
                                isUrl=False,
                                data="\"" +
                                     helpers.loadTextFile("tests/img/" +
                                                          "test_img_n" +
                                                          "ok_dim.txt") +
                                     "\""
                               )
                               )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_patch_user_avatar_img_form_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/avatar",
                               value=dict(
                                isUrl=False,
                                data="\"" +
                                     helpers.loadTextFile("tests/img/" +
                                                          "test_img_n" +
                                                          "ok_form.txt") +
                                     "\""
                               )
                               )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_patch_user_avatar_img_size_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/avatar",
                               value=dict(
                                isUrl=False,
                                data="\"" +
                                     helpers.loadTextFile("tests/img/" +
                                                          "test_img_n" +
                                                          "ok_size.txt") +
                                     "\""
                               )
                               )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_patch_user_avatar_img_invalid_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/testunituser_patch',
                           headers={'Content-Type': 'application/json',
                                    'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                               op="replace",
                               path="/avatar",
                               value=dict(
                                isUrl=False,
                                data="FakeIMG"
                               )
                               )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-2, r.json["code"])

    def test_delete_not_existing_user_should_return_not_found(self):
        r = self.app.delete('/api/v1/users/testunituser_delete_invalid',
                            headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_delete_existing_user_should_return_ok(self):
        r = self.app.delete('/api/v1/users/testunituser_delete',
                            headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(0, r.json["code"])

    def test_get_user_sessions_should_return_ok(self):
        r = self.app.get('/api/v1/users/testunituser_get/sessions',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_user_sessions_should_return_bad_request(self):
        r = self.app.get('/api/v1/users/testunituser_get_closed/sessions',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_user_sessions_should_return_not_found(self):
        r = self.app.get('/api/v1/users/testunituser_not_found/sessions',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_delete_closed_user_should_return_bad_request(self):
        r = self.app.delete('/api/v1/users/' +
                            'testunituser_get_closed',
                            headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_put_closed_user_should_return_bad_request(self):
        r = self.app.put('/api/v1/users/' +
                         'testunituser_get_closed',
                         headers={'X-Client-ID': aux_functions.X_Client_ID},
                         json=dict(
                              first_name="test",
                              last_name="test",
                              email="testunituser_get_closed@mail.com"
                              )
                         )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_patch_closed_user_should_return_bad_request(self):
        r = self.app.patch('/api/v1/users/' +
                           'testunituser_get_closed',
                           headers={'X-Client-ID': aux_functions.X_Client_ID},
                           json=dict(
                                   op="replace",
                                   path="/password",
                                   value="test"
                                   )
                           )
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-3, r.json["code"])

    def test_get_user_sessions_paging_should_return_ok(self):
        r = self.app.get('/api/v1/users/testunituser_get/sessions' +
                         '?start=0&limit=1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_user_sessions_paging_invalid_should_return_ok(self):
        r = self.app.get('/api/v1/users/testunituser_get/sessions' +
                         '?start=-1&limit=-1',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(True, len(r.json) > 0)

    def test_get_user_sessions_paging_invalid_should_return_bad_request(self):
        r = self.app.get('/api/v1/users/testunituser_get/sessions' +
                         '?start=a&limit=b',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.BAD_REQUEST, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_delete_all_user_sessions_should_return_ok(self):
        aux_functions.createSession("testunituser_delete", self)
        r2 = self.app.delete('/api/v1/users/testunituser_delete/sessions',
                             headers={'X-Client-ID':
                                      aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r2.status_code)
        self.assertEqual(0, r2.json["code"])

    def test_delete_all_user_no_sessions_should_return_not_found(self):
        r2 = self.app.delete('/api/v1/users/testunituser_delete_no/sessions',
                             headers={'X-Client-ID':
                                      aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r2.status_code)
        self.assertEqual(-1, r2.json["code"])

    def test_get_user_exists_should_return_not_found(self):
        r = self.app.get('/api/v1/users/testunituser_get_exists/exists',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.NOT_FOUND, r.status_code)
        self.assertEqual(-1, r.json["code"])

    def test_get_user_exists_existing_user_should_return_ok(self):
        r = self.app.get('/api/v1/users/testunituser_get/exists',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(0, r.json["code"])

    def test_get_user_exists_existing_email_return_ok(self):
        r = self.app.get('/api/v1/users/testunituser_get@mail.com/exists',
                         headers={'X-Client-ID': aux_functions.X_Client_ID})
        self.assertEqual(HTTPStatus.OK, r.status_code)
        self.assertEqual(1, r.json["code"])


if __name__ == '__main__':
    unittest.main()
