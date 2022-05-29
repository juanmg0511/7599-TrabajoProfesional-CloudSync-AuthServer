# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# src/sessions.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
import uuid
from datetime import datetime, timedelta
# Flask, para la implementacion del servidor REST
from flask import request
from flask_restful import Resource, reqparse
from http import HTTPStatus
# Google auth libraries for 'Sign in with Google'
from google.oauth2 import id_token
from google.auth.transport import requests
# Passlib para encriptar contrasenias
from passlib.apps import custom_app_context

# Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers


# Clase que define el endpoint para trabajar con sesiones
# Operaciones CRUD: Create, Read, Update, Delete
# verbo GET - listar sesiones activas
# verbo POST - crear sesion, si existe refresca el token
class AllSessions(Resource):
    # verbo GET - listar sesiones
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'All sessions requested.')
        AllSessionsResponseGet = []
        AllSessions = authServer.db.sessions.find()

        for existingSession in AllSessions:
            retrievedSession = {
                "id": str(existingSession["_id"]),
                "username": existingSession["username"],
                "session_token": existingSession["session_token"],
                "expires":  existingSession["expires"],
                "date_created": existingSession["date_created"]
            }
            AllSessionsResponseGet.append(retrievedSession)

        return helpers.return_request(AllSessionsResponseGet, HTTPStatus.OK)

    # verbo POST - crear sesion, si existe refresca el token
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
                                   args["username"] +
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
            existingAdminUser = authServer.db.adminusers.find_one(
                                    {"username": args["username"]}
                                )
        else:
            existingUser = authServer.db.users.find_one(
                                    {"username": args["username"]}
                                )

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
                                                    args["username"] +
                                                    "' with external service.")
                        try:
                            # Specify the CLIENT_ID of the app that accesses
                            # the backend:
                            idinfo = id_token.verify_oauth2_token(
                                token, requests.Request(),
                                authServer.google_client_id)

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
                                    authServer.session_length_admin)
                                )
                            ).isoformat()
                    else:
                        expiry_time = (
                            datetime.utcnow() +
                            timedelta(
                                minutes=int(
                                    authServer.session_length_user)
                                )
                            ).isoformat()
                    sessionToInsert = {
                        "username": args["username"],
                        "session_token": str(uuid.uuid1()),
                        "expires": expiry_time,
                        "date_created": datetime.utcnow().isoformat()
                    }
                    SessionResponsePost = sessionToInsert.copy()
                    authServer.db.sessions.insert_one(sessionToInsert)
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
                "message": "Bad request. Account '" + args["username"] +
                           "' is closed.",
                "data": None
            }
            return helpers.return_request(SessionResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        SessionResponsePost = {
            "code": -4,
            "message": "User '" + args["username"] + "' not found.",
            "data": None
        }
        return helpers.return_request(SessionResponsePost,
                                      HTTPStatus.UNAUTHORIZED)


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

        existingSession = authServer.db.sessions.find_one(
            {"session_token": token})
        if (existingSession is not None):
            # No hace falta chequear si el usuario de la sesion existe porque
            # borramos todas las sesiones existentes del un usuario al borrarlo
            if (datetime.utcnow()
               <
               datetime.fromisoformat(existingSession["expires"])):

                # Sesion valida, chequeamos si la sesion es de un admin
                isAdmin = False
                existingAdminUser = authServer.db.adminusers.find_one(
                    {"username": existingSession["username"]})
                if (existingAdminUser is not None):
                    isAdmin = True

                # Le sumamos un delta mas a la sesion
                if (isAdmin is True):
                    new_expiry = (
                        datetime.utcnow() +
                        timedelta(
                            minutes=int(
                                authServer.session_length_admin)
                            )
                        ).isoformat()
                else:
                    new_expiry = (
                        datetime.utcnow() +
                        timedelta(
                            minutes=int(
                                authServer.session_length_user)
                            )
                        ).isoformat()

                sessionToUpdate = {
                    "username": existingSession["username"],
                    "session_token": existingSession["session_token"],
                    "expires":  new_expiry,
                    "date_created": existingSession["date_created"]
                }
                SessionResponseGet = sessionToUpdate.copy()
                SessionResponseGet["id"] = str(existingSession["_id"])
                authServer.db.sessions.update_one(
                    {"session_token": token}, {'$set': sessionToUpdate})

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

        existingSession = authServer.db.sessions.find_one(
            {"session_token": token})
        if (existingSession is not None):

            authServer.db.sessions.delete_one({"session_token": token})

            SessionResponseDelete = {
                "code": 0,
                "message": "Session with token '" + token + "' deleted.",
                "data": None
            }
            return helpers.return_request(SessionResponseDelete, HTTPStatus.OK)

        SessionResponseDelete = {
            "code": 0,
            "message": "Session with token '" + token + "' not found.",
            "data": None
        }
        return helpers.return_request(SessionResponseDelete, HTTPStatus.OK)
