# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Unit test file, funciones auxiliares
# tests/aux_functions.py

# Importacion de las configuracion del Auth Server
import auth_server_config as config
# Importacion del archivo principal
import auth_server

# Toma el api key del auth server
# Se puede usar otro si así se desea
X_Client_ID = config.api_key


# Crea un usuario de prueba, sin usar la API
def createTestUserRaw(username):
    test_user = dict(
                    username=username,
                    first_name="test",
                    last_name="test",
                    contact=dict(
                        phone="1545642323",
                        email="test@mail.com"
                    )
    )

    return test_user


# Crea un usuario de prueba, usando la API
def createTestUser(username, cls):
    cls.app.post('/api/v1/users',
                 headers={'Content-Type': 'application/json',
                                          'X-Client-ID': X_Client_ID},
                 json=dict(
                     username=username,
                     password="password",
                     first_name="test",
                     last_name="test",
                     contact=dict(
                         phone="1545642323",
                         email="test@mail.com"
                         )
                     )
                 )


# Crea un usuario de prueba que usa servicio de autenticacion, usando la API
def createTestUserService(username, cls):
    cls.app.post('/api/v1/users',
                 headers={'Content-Type': 'application/json',
                                          'X-Client-ID': X_Client_ID},
                 json=dict(
                     username=username,
                     first_name="test",
                     last_name="test",
                     login_service=True,
                     contact=dict(
                         phone="1545642323",
                         email="test@mail.com"
                        )
                     )
                 )


# Cierra una cuenta de usuario de prueba, usando la API
def closeAccountTestUser(username, cls):
    r = cls.app.delete('/api/v1/users/' + username,
                       headers={'X-Client-ID': X_Client_ID})
    return r


# Borra la cuenta, sesiones y pedidos de recovery de un usuario de prueba,
# ***directamente de la base de datos***
def deleteTestUser(username):
    auth_server.db.users.delete_many({"username": username})
    auth_server.db.sessions.delete_many({"username": username})
    auth_server.db.recovery.delete_many({"username": username})


# Crea un usuario admin de prueba, usando la API
def createAdminTestUser(username, cls):
    cls.app.post('/api/v1/adminusers',
                 headers={'Content-Type': 'application/json',
                                          'X-Client-ID': X_Client_ID},
                 json=dict(
                     username=username,
                     password="password",
                     first_name="test",
                     last_name="test",
                     email="test@mail.com"
                    )
                 )


# Cierra una cuenta de usuario admin de prueba, usando la API
def closeAccountAdminTestUser(username, cls):
    r = cls.app.delete('/api/v1/adminusers/' + username,
                       headers={'X-Client-ID': X_Client_ID})
    return r


# Borra la cuenta y sesiones de un usuario admin de prueba,
# ***directamente de la base de datos***
def deleteAdminTestUser(username):
    auth_server.db.adminusers.delete_many({"username": username})
    auth_server.db.sessions.delete_many({"username": username})


# Crea una sesion de prueba para el usuario
def createSession(username, cls):
    r = cls.app.post('/api/v1/sessions',
                     headers={'Content-Type': 'application/json',
                                              'X-Client-ID': X_Client_ID},
                     json=dict(
                         username=username,
                         password="password"
                        )
                     )
    return r


# Crea una sesion de prueba para el usuario admin
def createSessionAdmin(username, cls):
    r = cls.app.post('/api/v1/sessions',
                     headers={'Content-Type': 'application/json',
                                              'X-Client-ID': X_Client_ID,
                                              'X-Admin': True},
                     json=dict(
                         username=username,
                         password="password"
                        )
                     )
    return r


# Crea un pedido de recovery de prueba para el usuario
def createRecoveryRequest(username, cls):
    r = cls.app.post('/api/v1/recovery',
                     headers={'Content-Type': 'application/json',
                                              'X-Client-ID': X_Client_ID},
                     json=dict(
                         username=username
                        )
                     )
    return r
