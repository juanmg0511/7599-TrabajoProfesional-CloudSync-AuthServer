# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file
# tests/test_helpers.py

# Importacion de librerias necesarias
import unittest
import logging
from http import HTTPStatus

# Importacion del archivo principal
import auth_server
from src import helpers
from tests import aux_functions


class HelpersTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = auth_server.app
        app.logger.setLevel(logging.CRITICAL)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        print("Starting testing helper methods of the auth server...")
        # Creamos los usuarios a ser utilizados durante los tests
        aux_functions.createTestUser("testunituser_post", cls)
        # Creamos las sesiones a ser utilizadas durante los tests
        aux_functions.createSession("testunituser_post", cls)
        # Creamos los recovery requests a ser utilizados durante los tests
        aux_functions.createRecoveryRequest("testunituser_post", cls)

    @classmethod
    def tearDownClass(cls):
        print("Finished testing helper methods of the auth server!")
        # Borramos los usuarios generados para los tests
        aux_functions.deleteTestUser("testunituser_post")

    def test_prune_sessions_should_return_0(self):
        r = helpers.prune_sessions()
        self.assertEqual(0, r)

    def test_prune_recovery_should_return_0(self):
        r = helpers.prune_recovery()
        self.assertEqual(0, r)

    def test_config_log_should_return_0(self):
        r = helpers.config_log()
        self.assertEqual(0, r)

    def test_handle_database_error_should_return_service_unavailable(self):
        r = helpers.handleDatabasebError("Test")
        self.assertEqual(HTTPStatus.SERVICE_UNAVAILABLE, r[1])
        self.assertEqual(-1, r[0]["code"])


if __name__ == '__main__':
    unittest.main()
