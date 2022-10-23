# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# src/sessions.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Manejo de tokens con Flask-JWT-Extended:
# https://content.breatheco.de/es/lesson/what-is-JWT-and-how-to-implement-with-Flask
# https://flask-jwt-extended.readthedocs.io/en/stable/api/#flask_jwt_extended.create_access_token
# https://flask-jwt-extended.readthedocs.io/en/stable/api/#flask_jwt_extended.decode_token

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
from datetime import datetime, timedelta
# Flask, para la implementacion del servidor REST
from flask_restful import Resource, reqparse
from flask import request
from http import HTTPStatus
# Flask-JWT-Extended para la generacion de tokens
from flask_jwt_extended import create_access_token
from flask_jwt_extended import decode_token
# Google auth libraries for 'Sign in with Google'
from google.oauth2 import id_token
from google.auth.transport import requests
# Passlib para encriptar contrasenias
from passlib.apps import custom_app_context

# Importacion de las configuracion del Auth Server
import auth_server_config as config
# Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers


# Clase que define el endpoint para trabajar con sesiones
# Operaciones CRUD: Create, Read, Update, Delete
# verbo GET - listar sesiones activas
# verbo POST - crear sesion, si existe refresca el token
# verbo DELETE - cerrar sesion de todos los usuarios,
# menos la sesion pasada por parametro
class AllSessions(Resource):
    # verbo GET - listar sesiones
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'All sessions requested.')

        try:
            parser = reqparse.RequestParser()
            # Primer registro de la collection a mostrar
            # El indice arranca en 0!
            parser.add_argument("start",
                                type=int,
                                required=False,
                                nullable=False)
            # Cantidad de registros de la collection a
            # mostrar por pagina
            # Si es igual a 0 es como si no estuviera
            parser.add_argument("limit",
                                type=int,
                                required=False,
                                nullable=False)
            # Texto para filtrar los resultados
            parser.add_argument("user_filter",
                                type=helpers.
                                non_empty_and_safe_filter_username,
                                required=False,
                                nullable=False)
            # Columna a utilizar para ordenar los resultados, si no se
            # incluye se trabaja con natural order
            parser.add_argument("sort_column",
                                type=helpers.
                                non_empty_string,
                                required=False,
                                nullable=False)
            # Indica el tipo de orden a utilizar en el ordenamiento, se
            # aplica independientemente de si es especificada una columna o
            # no. El valor por default es ASCENDENTE (1)
            parser.add_argument("sort_order",
                                type=int,
                                required=False,
                                nullable=False)
            args = parser.parse_args()
        except Exception:
            AllSessionsResponseGet = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(AllSessionsResponseGet,
                                          HTTPStatus.BAD_REQUEST)

        user_filter = args.get("user_filter", None)

        # Parseo de los parametros para el pagindo
        query_start = str(args.get("start", 0))
        if (query_start != "None"):
            query_start = int(query_start)
            if (query_start < 0):
                query_start = 0
        else:
            query_start = 0
        query_limit = str(args.get("limit", 0))
        if (query_limit != "None"):
            query_limit = int(query_limit)
            if (query_limit <= 0 or query_limit > int(config.page_max_size)):
                query_limit = int(config.page_max_size)
        else:
            query_limit = int(config.page_max_size)

        # Se construye el query para filtrar en base a los parametros
        # opcionales
        find_query = {}
        if (user_filter is not None):
            find_query["username"] = {
                "$regex": ".*" + str(user_filter) + ".*",
                "$options": 'i'
            }

        # Se construye el sort para ordenar el query. Si no se especifica,
        # se trabaja con el natural order
        query_sort_column = args.get("sort_column", None)
        query_sort_order = args.get("sort_order", None)
        if (query_sort_column is None):
            query_sort_column = "$natural"
        if (
            (query_sort_order is not None) and
            (query_sort_order != -1)
           ):
            query_sort_order = 1

        # Operacion de base de datos
        try:
            AllSessions = authServer.db.sessions.\
                          find(find_query).\
                          skip(query_start).\
                          limit(query_limit).\
                          sort(query_sort_column, query_sort_order)
            AllSessionsCount = authServer.db.sessions.\
                count_documents(find_query)
        except Exception as e:
            return helpers.handleDatabasebError(e)

        # Calculo de las URL hacia anterior y siguiente
        start_previous = query_start - query_limit
        start_next = query_start + query_limit
        if (start_previous < 0
           or (start_previous >= AllSessionsCount)
           or (query_start == 0 and query_limit == 0)
           or (query_limit == 0)):
            url_previous = None
        else:
            url_previous = request.path +\
                           "?start=" +\
                           str(start_previous) +\
                           "&limit=" +\
                           str(query_limit)

        if (start_next >= AllSessionsCount
           or (query_start == 0 and query_limit == 0)
           or (query_limit == 0)):
            url_next = None
        else:
            url_next = request.path +\
                       "?start=" +\
                       str(start_next) +\
                       "&limit=" +\
                       str(query_limit)

        try:
            AllSessionsResultsGet = []
            for existingSession in AllSessions:
                retrievedSession = {
                    "id": str(existingSession["_id"]),
                    "username": existingSession["username"],
                    "user_role": existingSession["user_role"],
                    "session_token": existingSession["session_token"],
                    "expired": (datetime.utcnow() >
                                datetime.
                                fromisoformat(existingSession["expires"])),
                    "expires": existingSession["expires"],
                    "date_created": existingSession["date_created"]
                }
                AllSessionsResultsGet.append(retrievedSession)
        except Exception as e:
            return helpers.handleDatabasebError(e)

        # Construimos la respuesta paginada
        AllSessionsResponseGet = {
            "total": AllSessionsCount,
            "limit": query_limit,
            "next": url_next,
            "previous": url_previous,
            "results": AllSessionsResultsGet
        }

        return helpers.return_request(AllSessionsResponseGet, HTTPStatus.OK)

    # verbo POST - crear sesion
    @helpers.require_apikey
    @helpers.log_reqId
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("username", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("password", type=helpers.non_empty_string,
                                required=False, nullable=False)
            parser.add_argument("login_service_token",
                                type=helpers.non_empty_string,
                                required=False, nullable=False)
            args = parser.parse_args()
        except Exception:
            SessionResponsePost = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(SessionResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        authServer.app.logger.info(helpers.log_request_id() +
                                   "New session for user '" +
                                   str.lower(args["username"]) +
                                   "' requested.")

        # Vemos si el usuario es un admin o no
        # isAdmin = helpers.non_empty_bool(
        #               request.headers.get("X-Admin", False)
        #           )
        isAdmin = str(request.headers.get("X-Admin", "False"))
        if (str(isAdmin).lower().replace("\"", "").replace("'", "") == "true"):
            isAdmin = True
        else:
            isAdmin = False

        # Buscamos el usuario en ambas collections
        existingAdminUser = None
        existingUser = None
        if (isAdmin is True):
            try:
                existingAdminUser = authServer.db.adminusers.find_one(
                                        {"username":
                                            str.lower(args["username"])}
                                    )
            except Exception as e:
                return helpers.handleDatabasebError(e)
        else:
            try:
                existingUser = authServer.db.users.find_one(
                                        {"username":
                                            str.lower(args["username"])}
                                    )
            except Exception as e:
                return helpers.handleDatabasebError(e)

        # Validamos el login del usuario
        if ((existingUser is not None) or (existingAdminUser is not None)):
            is_service = False
            valid_password = False
            valid_login = False
            try:
                if (existingUser is not None):
                    if (existingUser["login_service"] is False):
                        error_code = -3
                        # Debe proporcionar una password, y no debe estar vacia
                        if (args["password"] is None):
                            raise ValueError("Password is required" +
                                             " without login service.")
                        # No debe proporcionar un token
                        if (args["login_service_token"] is not None):
                            raise ValueError("Must not supply token" +
                                             " without login service.")
                        valid_password = custom_app_context.verify(
                                            args["password"],
                                            existingUser["password"])
                    else:
                        is_service = True
                        error_code = -4
                        # No debe proporcionar una password
                        if (args["password"] is not None):
                            raise ValueError("Must not supply password" +
                                             " with login service.")
                        # Debe proporcionar un token, y no debe estar vacio
                        if (args["login_service_token"] is not None):
                            token = args["login_service_token"]
                        else:
                            raise ValueError("Token is required" +
                                             " with login service.")

                        # https://developers.google.com/identity/sign-in/android/backend-auth
                        # (Receive token by HTTPS POST)
                        # ...
                        authServer.app.logger.debug(helpers.log_request_id() +
                                                    "Checking valid login" +
                                                    " for user '" +
                                                    str.lower(
                                                        args["username"]) +
                                                    "' with external service.")
                        try:
                            # Specify the CLIENT_ID of the app that accesses
                            # the backend:
                            idinfo = id_token.verify_oauth2_token(
                                token, requests.Request(),
                                config.google_client_id)

                            # Or, if multiple clients access the
                            # backend server:
                            # idinfo = id_token.verify_oauth2_token(
                            #   token, requests.Request())
                            # if idinfo['aud'] not in [CLIENT_ID_1,
                            #                          CLIENT_ID_2,
                            #                          CLIENT_ID_3]:
                            #   raise ValueError('Could not verify audience.')

                            if (idinfo['iss']
                               not in
                               ['accounts.google.com',
                               'https://accounts.google.com']):
                                raise ValueError('Wrong issuer.')

                            # If auth request is from a G Suite domain:
                            # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
                            #     raise ValueError('Wrong hosted domain.')

                            # ID token is valid. Get the user's Google Account
                            # ID from the decoded token.
                            userid = idinfo['sub']
                            useremail = idinfo['email']
                            # Esta autorizado por Google - chequeamos los datos
                            # {
                            #    # These six fields are included in all
                            #    # Google ID Tokens.
                            #    "iss": "https://accounts.google.com",
                            #    "sub": "110169484474386276334",
                            #    "azp": "1008719970978-hb24n2dstb40o45d4feu" +
                            #           "o2ukqmcc6381.apps.googleusercontent.com",
                            #    "aud": "1008719970978-hb24n2dstb40o45d4feu" +
                            #           "o2ukqmcc6381.apps.googleusercontent.com",
                            #    "iat": "1433978353",
                            #    "exp": "1433981953",
                            #
                            #    These seven fields are only included when the
                            #    user has granted the "profile" and
                            #    "email" OAuth scopes to the application.
                            #    "email": "testuser@gmail.com",
                            #    "email_verified": "true",
                            #    "name" : "Test User",
                            #    "picture": "https://lh4.googleusercontent" +
                            #               ".com/-kYgzyAWpZzJ/ABCDEFGHI/A" +
                            #               "AAJKLMNOP/tIXL9Ir44LE/s99-c/p" +
                            #               "hoto.jpg",
                            #    "given_name": "Test",
                            #    "family_name": "User",
                            #    "locale": "en"
                            # }
                            # Para chequear el mail necesitamos
                            # grantear el Profile
                            if (useremail == existingUser["username"]):
                                # Es el usuario
                                authServer.app.logger.debug(
                                    helpers.log_request_id() + "Authorized.")
                                authServer.app.logger.debug(
                                    helpers.log_request_id() + str(userid))
                                valid_login = True

                        except Exception as loginServiceExcept:
                            # Invalid token
                            # Si no esta autorizado por Google,
                            # dejamos la variable en false
                            authServer.app.logger.debug(
                                helpers.log_request_id() +
                                "Not authorized. Failed.")
                            authServer.app.logger.debug(
                                helpers.log_request_id() + "Message: " +
                                str(loginServiceExcept))
                    closed = existingUser["account_closed"]
                if (existingAdminUser is not None):
                    error_code = -5
                    # Debe proporcionar una password, y no debe estar vacia
                    if (args["password"] is None):
                        raise ValueError("Password is required" +
                                         " without login service.")
                    # No debe proporcionar un token
                    if (args["login_service_token"] is not None):
                        raise ValueError("Must not supply token without" +
                                         " login service.")
                    valid_password = custom_app_context.verify(
                        args["password"], existingAdminUser["password"])
                    closed = existingAdminUser["account_closed"]
            except ValueError as v:
                SessionResponsePost = {
                    "code": error_code,
                    "message": "Bad request. Wrong combination of" +
                               "'login_service' and 'password'," +
                               " please see API documentation.",
                    "data": str(v)
                }
                return helpers.return_request(SessionResponsePost,
                                              HTTPStatus.BAD_REQUEST)

            if (closed is False):
                if ((valid_password is True) or (valid_login is True)):
                    if (isAdmin is True):
                        expiry_time = (
                            datetime.utcnow() +
                            timedelta(
                                minutes=int(
                                    config.session_length_admin)
                                )
                            ).isoformat()
                    else:
                        expiry_time = (
                            datetime.utcnow() +
                            timedelta(
                                minutes=int(
                                    config.session_length_user)
                                )
                            ).isoformat()

                    # Generamos el token, con formato JWT
                    # Como manejamos sesiones stateful, el venicimiento se
                    # guarda en el servidor
                    try:
                        token = create_access_token(identity=str.lower(
                                                        args["username"]),
                                                    expires_delta=False)
                    except Exception:
                        SessionResponsePost = {
                            "code": -1,
                            "message": "Error creating acces token.",
                            "data": None
                        }
                        return helpers.return_request(
                            SessionResponsePost,
                            HTTPStatus.SERVICE_UNAVAILABLE)

                    sessionToInsert = {
                        "username": str.lower(args["username"]),
                        "user_role": "admin" if isAdmin else "user",
                        "session_token": token,
                        "expires": expiry_time,
                        "date_created": datetime.utcnow().isoformat()
                    }
                    SessionResponsePost = sessionToInsert.copy()
                    try:
                        authServer.db.sessions.insert_one(sessionToInsert)
                    except Exception as e:
                        return helpers.handleDatabasebError(e)
                    id_sessionToInsert = str(sessionToInsert["_id"])
                    SessionResponsePost["id"] = id_sessionToInsert

                    return helpers.return_request(SessionResponsePost,
                                                  HTTPStatus.CREATED)

                error_code_password = -2
                message = "Wrong username or password."
                if (is_service is True):
                    error_code_password = -3
                    message = "Identity validation with external login" + \
                              " service provider failed."
                SessionResponsePost = {
                    "code": error_code_password,
                    "message": message,
                    "data": None
                }
                return helpers.return_request(SessionResponsePost,
                                              HTTPStatus.UNAUTHORIZED)

            SessionResponsePost = {
                "code": -2,
                "message": "Bad request. Account '" +
                           str.lower(args["username"]) +
                           "' is closed.",
                "data": None
            }
            return helpers.return_request(SessionResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        SessionResponsePost = {
            "code": -4,
            "message": "User '" +
                       str.lower(args["username"]) +
                       "' not found.",
            "data": None
        }
        return helpers.return_request(SessionResponsePost,
                                      HTTPStatus.UNAUTHORIZED)

    # verbo DELETE - cerrar sesion de todos los usuarios,
    # menos la sesion pasada por parametro
    @helpers.require_apikey
    @helpers.log_reqId
    def delete(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("token", type=helpers.non_empty_string,
                                required=True, nullable=False)
            args = parser.parse_args()
        except Exception:
            RecoveryResponsePost = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(RecoveryResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        authServer.app.logger.info(helpers.log_request_id() +
                                   "Session deletion for all users " +
                                   "except token '" +
                                   args["token"] +
                                   "' requested.")

        try:
            existingSession = authServer.db.sessions.find_one({
                "session_token": args["token"]
            })
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingSession is not None):

            try:
                authServer.db.sessions.delete_many({
                    "session_token": {"$ne": args["token"]}
                })
            except Exception as e:
                return helpers.handleDatabasebError(e)

            SessionResponseDelete = {
                "code": 0,
                "message": "All sessions except token '" +
                           args["token"] +
                           "' deleted.",
                "data": None
            }
            return helpers.return_request(SessionResponseDelete, HTTPStatus.OK)

        SessionResponseDelete = {
            "code": -2,
            "message": "Session with token '" + args["token"] + "' not found.",
            "data": None
        }
        return helpers.return_request(SessionResponseDelete,
                                      HTTPStatus.NOT_FOUND)


# Clase que define el endpoint para trabajar con sesiones
# Operaciones CRUD: Create, Read, Update, Delete
# verbo GET - checkear sesion
# verbo DELETE - cerrar sesion
class Session(Resource):

    # verbo GET - checkear sesion
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self, token):
        authServer.app.logger.info(helpers.log_request_id() +
                                   "Session with token '" + token +
                                   "' requested.")
        try:
            existingSession = authServer.db.sessions.find_one(
                {"session_token": token})
        except Exception as e:
            return helpers.handleDatabasebError(e)

        # La sesion existe
        if (existingSession is not None):
            # No hace falta chequear si el usuario de la sesion existe porque
            # borramos todas las sesiones existentes del un usuario al borrarlo
            try:
                # Chequeamos si el token suministrado es valido
                token_data = decode_token(token)

                # Vemos si el usuario coincide con el de la sesion
                if (token_data["identity"] != existingSession["username"]):
                    raise(Exception)
            except Exception:
                SessionResponseGet = {
                    "code": -1,
                    "message": "Invalid token '" + token + "' supplied.",
                    "data": None
                }
                return helpers.return_request(SessionResponseGet,
                                              HTTPStatus.UNAUTHORIZED)

            # Revisamos si la sesion esta vencida
            if (datetime.utcnow()
               <
               datetime.fromisoformat(existingSession["expires"])):

                # Sesion valida, chequeamos si la sesion es de un admin
                isAdmin = False
                try:
                    existingAdminUser = authServer.db.adminusers.find_one(
                        {"username": existingSession["username"]})
                except Exception as e:
                    return helpers.handleDatabasebError(e)
                if (existingAdminUser is not None):
                    isAdmin = True

                # Le sumamos un delta mas a la sesion
                if (isAdmin is True):
                    new_expiry = (
                        datetime.utcnow() +
                        timedelta(
                            minutes=int(
                                config.session_length_admin)
                            )
                        ).isoformat()
                else:
                    new_expiry = (
                        datetime.utcnow() +
                        timedelta(
                            minutes=int(
                                config.session_length_user)
                            )
                        ).isoformat()

                sessionToUpdate = {
                    "username": existingSession["username"],
                    "user_role": existingSession["user_role"],
                    "session_token": existingSession["session_token"],
                    "expires":  new_expiry,
                    "date_created": existingSession["date_created"]
                }
                SessionResponseGet = sessionToUpdate.copy()
                SessionResponseGet["id"] = str(existingSession["_id"])
                SessionResponseGet["expired"] = (datetime.utcnow() >
                                                 datetime.
                                                 fromisoformat(new_expiry))

                try:
                    authServer.db.sessions.update_one(
                        {"session_token": token}, {'$set': sessionToUpdate})
                except Exception as e:
                    return helpers.handleDatabasebError(e)

                authServer.app.logger.debug(helpers.log_request_id() +
                                            "Valid session token provided: " +
                                            "\"" +
                                            sessionToUpdate["session_token"] +
                                            "\".")
                authServer.app.logger.info(helpers.log_request_id() +
                                           "Valid user \"" +
                                           sessionToUpdate["username"] +
                                           "\" session with " +
                                           sessionToUpdate["user_role"] +
                                           " privileges.")

                return helpers.return_request(SessionResponseGet,
                                              HTTPStatus.OK)

            SessionResponseGet = {
                "code": -2,
                "message": "Session with token '" + token + "' has expired.",
                "data": None
            }
            return helpers.return_request(SessionResponseGet,
                                          HTTPStatus.UNAUTHORIZED)

        SessionResponseGet = {
            "code": -3,
            "message": "No session with token '" + token + "' was found.",
            "data": None
        }
        return helpers.return_request(SessionResponseGet,
                                      HTTPStatus.UNAUTHORIZED)

    # verbo DELETE - cerrar sesion
    @helpers.require_apikey
    @helpers.log_reqId
    def delete(self, token):
        authServer.app.logger.info(helpers.log_request_id() +
                                   "Session deletion with token '" + token +
                                   "' requested.")

        try:
            existingSession = authServer.db.sessions.find_one({
                "session_token": token
            })
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingSession is not None):

            try:
                authServer.db.sessions.delete_one({
                    "session_token": token
                })
            except Exception as e:
                return helpers.handleDatabasebError(e)

            SessionResponseDelete = {
                "code": 0,
                "message": "Session with token '" + token + "' deleted.",
                "data": None
            }
            return helpers.return_request(SessionResponseDelete, HTTPStatus.OK)

        SessionResponseDelete = {
            "code": -1,
            "message": "Session with token '" + token + "' not found.",
            "data": None
        }
        return helpers.return_request(SessionResponseDelete,
                                      HTTPStatus.NOT_FOUND)
