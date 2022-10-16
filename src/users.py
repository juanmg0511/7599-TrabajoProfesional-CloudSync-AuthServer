# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# src/users.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
from datetime import datetime
# Flask, para la implementacion del servidor REST
from flask_restful import Resource, reqparse
from flask import request
from http import HTTPStatus
# Passlib para encriptar contrasenias
from passlib.apps import custom_app_context

# Importacion de las configuracion del Auth Server
import auth_server_config as config
# Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers


# Clase que define el endpoint para trabajar con usuarios
# Operaciones CRUD: Create, Read, Update, Delete
# verbo GET - listar usuarios
# verbo POST - nuevo usario
class AllUsers(Resource):
    # verbo GET - listar usuarios
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'All users requested.')

        try:
            parser = reqparse.RequestParser()
            parser.add_argument("show_closed",
                                type=helpers.non_empty_string,
                                required=False,
                                nullable=False)
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
            args = parser.parse_args()
        except Exception:
            AllUsersResponseGet = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(AllUsersResponseGet,
                                          HTTPStatus.BAD_REQUEST)

        show_closed = str(args.get("show_closed", "False"))
        if (str(show_closed).lower().replace("\"", "").replace("'", "")
           ==
           "true"):
            show_closed = True
        else:
            show_closed = False
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
        if (show_closed is False):
            find_query["account_closed"] = False
        if (user_filter is not None):
            find_query["username"] = {
                "$regex": ".*" + str(user_filter) + ".*",
                "$options": 'i'
            }

        # Operacion de base de datos
        try:
            allUsers = authServer.db.users.\
                        find(find_query).\
                        skip(query_start).\
                        limit(query_limit)
            allUsersCount = authServer.db.users.\
                count_documents(find_query)
        except Exception as e:
            return helpers.handleDatabasebError(e)

        # Calculo de las URL hacia anterior y siguiente
        start_previous = query_start - query_limit
        start_next = query_start + query_limit
        if (start_previous < 0
           or (start_previous >= allUsersCount)
           or (query_start == 0 and query_limit == 0)
           or (query_limit == 0)):
            url_previous = None
        else:
            url_previous = request.path +\
                           "?start=" +\
                           str(start_previous) +\
                           "&limit=" +\
                           str(query_limit)

        if (start_next >= allUsersCount
           or (query_start == 0 and query_limit == 0)
           or (query_limit == 0)):
            url_next = None
        else:
            url_next = request.path +\
                       "?start=" +\
                       str(start_next) +\
                       "&limit=" +\
                       str(query_limit)

        AllUsersResultsGet = []
        for existingUser in allUsers:

            # Operacion de base de datos
            try:
                userSessionsCount = \
                    authServer.db.sessions.\
                    count_documents({
                        "username": existingUser["username"],
                        "expires": {"$gt": datetime.utcnow().isoformat()}
                    })
            except Exception as e:
                return helpers.handleDatabasebError(e)

            retrievedUser = {
                "id": str(existingUser["_id"]),
                "username": existingUser["username"],
                "first_name": existingUser["first_name"],
                "last_name":  existingUser["last_name"],
                "contact": existingUser["contact"],
                # Usar el endpoint dedicado para obtener el avatar de
                # los usuarios
                "avatar": "...",
                "login_service": existingUser["login_service"],
                "online": True if (userSessionsCount > 0) else False,
                "account_closed": existingUser["account_closed"],
                "date_created": existingUser["date_created"],
                "date_updated": existingUser["date_updated"]
            }
            AllUsersResultsGet.append(retrievedUser)

        # Construimos la respuesta paginada
        AllUsersResponseGet = {
            "total": allUsersCount,
            "limit": query_limit,
            "next": url_next,
            "previous": url_previous,
            "results": AllUsersResultsGet
        }

        return helpers.return_request(AllUsersResponseGet, HTTPStatus.OK)

    # verbo POST - nuevo usario
    @helpers.require_apikey
    @helpers.log_reqId
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("username",
                                type=helpers.non_empty_and_safe_username,
                                required=True, nullable=False)
            parser.add_argument("password",
                                type=helpers.non_empty_and_valid_password,
                                required=False, nullable=False)
            parser.add_argument("first_name", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("last_name", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("contact", type=dict,
                                required=True, nullable=False)
            parser.add_argument("avatar", type=dict,
                                required=False, nullable=True)
            parser.add_argument("login_service", type=helpers.non_empty_bool,
                                required=False, nullable=False)
            args = parser.parse_args()
        except Exception:
            UserResponsePost = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(UserResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        # Validacion requeridos en contact
        try:
            email = helpers.non_empty_email(args["contact"].get("email", ""))
            phone = helpers.non_empty_string(args["contact"].get("phone", ""))
        except Exception:
            UserResponsePost = {
                "code": -2,
                "message": "Bad request. Wrong format for 'contact'.",
                "data": None
            }
            return helpers.return_request(UserResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        # Validacion de avatar
        if (isinstance(args["avatar"], dict)):
            try:
                isUrl = helpers.\
                        non_empty_bool(args["avatar"].get("isUrl", ""))
                if (isUrl is True):
                    data = helpers.\
                           non_empty_url(args["avatar"].get("data", ""))
                else:
                    data = helpers.\
                           non_empty_image(args["avatar"].get("data", ""))

            except Exception:
                UserResponsePost = {
                    "code": -3,
                    "message": "Bad request. Wrong format for 'avatar'.",
                    "data": None
                }
                return helpers.return_request(UserResponsePost,
                                              HTTPStatus.BAD_REQUEST)
        else:
            isUrl = None
            data = None

        # Validacion del tipo de usuario
        # Por default es false, para que el cambio sea transparente
        login_service = False
        if ((args["login_service"] is True)
           or
           (args["login_service"] is False)):
            login_service = args["login_service"]

        try:
            if (login_service is True):
                # Si es true, no debe proporcionar una password
                if (args["password"] is not None):
                    raise ValueError("Must not supply password" +
                                     " with login service.")

            else:
                # Si es false, debe proporcionar una password
                # no debe estar vacia
                if (args["password"] is not None):
                    password = args["password"]
                else:
                    raise ValueError("Password is required" +
                                     " without login service.")

        except ValueError as v:
            UserResponsePost = {
                "code": -4,
                "message": "Bad request. Wrong combination of" +
                           " 'login_service' and 'password', please" +
                           " see API documentation.",
                "data": str(v)
            }
            return helpers.return_request(UserResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        authServer.app.logger.info(helpers.log_request_id() +
                                   "New user '" +
                                   str.lower(args["username"]) +
                                   "' requested.")

        try:
            existingUser = \
                authServer.db.users.find_one(
                    {"username": str.lower(args["username"])})
            existingAdminUser = \
                authServer.db.adminusers.find_one(
                    {"username": str.lower(args["username"])})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if ((existingUser is not None) or (existingAdminUser is not None)):
            UserResponsePost = {
                "code": -5,
                "message": "Bad request. User '" +
                           str.lower(args["username"]) +
                           "' already exists.",
                "data": None
            }
            return helpers.return_request(UserResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        userToInsert = {
            "username": str.lower(args["username"]),
            "first_name": args["first_name"],
            "last_name": args["last_name"],
            "contact": {
                            "email": email,
                            "phone": phone
                        },
            "avatar": {
                        "isUrl": isUrl,
                        "data": data
                      },
            "account_closed": False,
            "login_service": login_service,
            "date_created": datetime.utcnow().isoformat(),
            "date_updated": None
        }
        if (login_service is False):
            userToInsert["password"] = custom_app_context.hash(password)
        UserResponsePost = userToInsert.copy()
        try:
            authServer.db.users.insert_one(userToInsert)
        except Exception as e:
            return helpers.handleDatabasebError(e)
        id_userToInsert = str(userToInsert["_id"])
        UserResponsePost["id"] = id_userToInsert
        UserResponsePost.pop("password", None)

        return helpers.return_request(UserResponsePost, HTTPStatus.CREATED)


# Clase que define el endpoint para trabajar con usuarios
# Operaciones CRUD: Create, Read, Update, Delete
# verbo GET - leer usuario
# verbo PUT - actualizar usuario completo (sin contrasenia)
# verbo PATCH - actualizar contrasenia. solo permite op=replace y path=password
# verbo DELETE - borrar usuario
class User(Resource):

    # verbo GET - leer usuario
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self, username):
        authServer.app.logger.info(helpers.log_request_id() + "User '" +
                                   username + "' information requested.")

        try:
            existingUser = authServer.db.users.find_one({"username": username})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingUser is not None):

            try:
                userSessionsCount = \
                    authServer.db.sessions.\
                    count_documents({
                        "username": existingUser["username"],
                        "expires": {"$gt": datetime.utcnow().isoformat()}
                    })
            except Exception as e:
                return helpers.handleDatabasebError(e)

            UserResponseGet = {
                "id": str(existingUser["_id"]),
                "username": existingUser["username"],
                "first_name": existingUser["first_name"],
                "last_name": existingUser["last_name"],
                "contact": existingUser["contact"],
                "avatar": existingUser["avatar"],
                "login_service": existingUser["login_service"],
                "online": True if (userSessionsCount > 0) else False,
                "account_closed": existingUser["account_closed"],
                "date_created": existingUser["date_created"],
                "date_updated": existingUser["date_updated"]
            }
            return helpers.return_request(UserResponseGet, HTTPStatus.OK)

        UserResponseGet = {
            "code": -1,
            "message": "User '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(UserResponseGet, HTTPStatus.NOT_FOUND)

    # verbo PUT - actualizar usuario completo (sin contrasenia)
    @helpers.require_apikey
    @helpers.log_reqId
    def put(self, username):

        # Pasamos el usuario que viene en el path a minusculas
        username = str.lower(username)
        authServer.app.logger.info(helpers.log_request_id() +
                                   "User '" +
                                   username +
                                   "' update requested.")

        try:
            parser = reqparse.RequestParser()
            parser.add_argument("first_name", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("last_name", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("contact", type=dict,
                                required=True, nullable=False)
            parser.add_argument("avatar", type=dict,
                                required=False, nullable=True)
            args = parser.parse_args()
        except Exception:
            UserResponsePost = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(UserResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        # Validacion requeridos en contact
        try:
            email = helpers.non_empty_email(args["contact"].get("email", ""))
            phone = helpers.non_empty_string(args["contact"].get("phone", ""))
        except Exception:
            UserResponsePost = {
                "code": -2,
                "message": "Bad request. Wrong format for 'contact'.",
                "data": None
            }
            return helpers.return_request(UserResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        # Validacion de avatar
        if (isinstance(args["avatar"], dict)):
            try:
                isUrl = helpers.\
                        non_empty_bool(args["avatar"].get("isUrl", ""))
                if (isUrl is True):
                    data = helpers.\
                           non_empty_url(args["avatar"].get("data", ""))
                else:
                    data = helpers.\
                           non_empty_image(args["avatar"].get("data", ""))

            except Exception:
                UserResponsePost = {
                    "code": -3,
                    "message": "Bad request. Wrong format for 'avatar'.",
                    "data": None
                }
                return helpers.return_request(UserResponsePost,
                                              HTTPStatus.BAD_REQUEST)
        else:
            isUrl = None
            data = None

        try:
            existingUser = authServer.db.users.find_one({"username": username})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):

                if (isUrl is None):
                    isUrl = existingUser["avatar"]["isUrl"]
                    data = existingUser["avatar"]["data"]

                userToUpdate = {
                    "first_name": args["first_name"],
                    "last_name": args["last_name"],
                    "contact": {
                        "email": email,
                        "phone": phone
                    },
                    "avatar": {
                        "isUrl": isUrl,
                        "data": data
                      },
                    "login_service": existingUser["login_service"],
                    "account_closed": existingUser["account_closed"],
                    "date_created": existingUser["date_created"],
                    "date_updated": datetime.utcnow().isoformat()
                }

                UserResponsePut = userToUpdate.copy()
                try:
                    authServer.db.users.update_one(
                        {"username": username}, {'$set': userToUpdate})
                except Exception as e:
                    return helpers.handleDatabasebError(e)
                id_userToUpdate = str(existingUser["_id"])
                UserResponsePut["username"] = existingUser["username"]
                UserResponsePut["id"] = id_userToUpdate

                return helpers.return_request(UserResponsePut, HTTPStatus.OK)

            UserResponsePut = {
                "code": -4,
                "message": "User '" + username + "' account is closed.",
                "data:": None
            }
            return helpers.return_request(UserResponsePut,
                                          HTTPStatus.BAD_REQUEST)

        UserResponsePut = {
            "code": -1,
            "message": "User '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(UserResponsePut, HTTPStatus.NOT_FOUND)

    # verbo PATCH - actualizar contrasenia.
    # solo permite op=replace y path=password / path=avatar
    # { "op": "replace", "path": "/password", "value": "" }
    # { "op": "replace", "path": "/avatar", "value": "" }
    @helpers.require_apikey
    @helpers.log_reqId
    def patch(self, username):

        # Pasamos el usuario que viene en el path a minusculas
        username = str.lower(username)
        authServer.app.logger.info(helpers.log_request_id() +
                                   "Password or Avatar " +
                                   "modification for user '" +
                                   username +
                                   "' requested.")
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("op", type=helpers.non_empty_string,
                                required=True, nullable=False,
                                choices=['replace'])
            parser.add_argument("path", type=helpers.non_empty_string,
                                required=True, nullable=False,
                                choices=['/password', '/avatar'])
            parser.add_argument("value", type=helpers.non_empty_argument,
                                required=True, nullable=False)
            args = parser.parse_args()
        except Exception:
            UserResponsePatch = {
                "code": -1,
                "message": "Bad request. Wrong arguments," +
                           " please see API documentation.",
                "data": None
            }
            return helpers.return_request(UserResponsePatch,
                                          HTTPStatus.BAD_REQUEST)

        if (args["path"] == "/avatar"):
            try:
                isUrl = helpers.\
                        non_empty_bool(args["value"].get("isUrl", ""))
                if (isUrl is True):
                    data = helpers.\
                           non_empty_url(args["value"].get("data", ""))
                else:
                    data = helpers.\
                           non_empty_image(args["value"].get("data", ""))

            except Exception:
                UserResponsePatch = {
                    "code": -2,
                    "message": "Bad request. Wrong format for 'value'.",
                    "data": None
                }
                return helpers.return_request(UserResponsePatch,
                                              HTTPStatus.BAD_REQUEST)

        try:
            existingUser = authServer.db.users.find_one({"username": username})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):
                if (args["path"] == '/password'):
                    if (existingUser["login_service"] is False):
                        try:
                            existingUser["password"] = \
                                custom_app_context.\
                                hash(helpers.non_empty_and_valid_password(
                                    args["value"]))
                        except Exception:
                            userResponsePatch = {
                                "code": -1,
                                "message": "Invalid password.",
                                "data:": None
                            }
                            return helpers.\
                                return_request(userResponsePatch,
                                               HTTPStatus.BAD_REQUEST)
                    else:
                        userResponsePatch = {
                            "code": -4,
                            "message": "User '" +
                                       username +
                                       "' uses a login service," +
                                       " can't change password.",
                            "data:": None
                        }
                        return helpers.return_request(userResponsePatch,
                                                      HTTPStatus.BAD_REQUEST)
                else:
                    existingUser["avatar"] = {
                                                "isUrl": isUrl,
                                                "data": data
                                             }
                existingUser["date_updated"] = datetime.utcnow().isoformat()
                try:
                    authServer.db.users.update_one(
                        {"username": username}, {'$set': existingUser})
                except Exception as e:
                    return helpers.handleDatabasebError(e)

                userResponsePatch = {
                    "code": 0,
                    "message": "User '" + username + "' path '" +
                               args["path"] + "' updated.",
                    "data:": None
                }
                return helpers.return_request(userResponsePatch, HTTPStatus.OK)

            userResponsePatch = {
                "code": -3,
                "message": "User '" + username + "' account is closed.",
                "data:": None
            }
            return helpers.return_request(userResponsePatch,
                                          HTTPStatus.BAD_REQUEST)

        userResponsePatch = {
            "code": -1,
            "message": "User '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(userResponsePatch, HTTPStatus.NOT_FOUND)

    # verbo DELETE - borrar usuario
    @helpers.require_apikey
    @helpers.log_reqId
    def delete(self, username):

        # Pasamos el usuario que viene en el path a minusculas
        username = str.lower(username)
        authServer.app.logger.info(helpers.log_request_id() +
                                   "User '" +
                                   username +
                                   "' close account requested.")

        try:
            existingUser = authServer.db.users.find_one({"username": username})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):

                try:
                    authServer.db.users.update_one(
                        {"username": username},
                        {'$set':
                            {'account_closed': True,
                             'date_updated': datetime.utcnow().isoformat()}})
                    authServer.db.sessions.delete_many({"username": username})
                    authServer.db.recovery.delete_many({"username": username})
                except Exception as e:
                    return helpers.handleDatabasebError(e)

                UserResponseDelete = {
                    "code": 0,
                    "message": "User '" + username +
                               "' marked as closed account.",
                    "data": None
                }
                return helpers.return_request(UserResponseDelete,
                                              HTTPStatus.OK)

            UserResponseDelete = {
                "code": -1,
                "message": "User '" + username +
                           "' account is already closed.",
                "data": None
            }
            return helpers.return_request(UserResponseDelete,
                                          HTTPStatus.BAD_REQUEST)

        UserResponseDelete = {
            "code": -1,
            "message": "User '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(UserResponseDelete, HTTPStatus.NOT_FOUND)


# Clase que define el endpoint para obtener las sesiones de un usuario
# verbo GET - obtener sesiones vigentes del usuario
# verbo DELETE - cerrar todas las sesiones del usuario
class UserSessions(Resource):

    # verbo GET - obtener sesiones vigentes del usuario
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self, username):

        # Pasamos el usuario que viene en el path a minusculas
        username = str.lower(username)
        authServer.app.logger.info(helpers.log_request_id() + "User '" +
                                   username + "' sessions requested.")

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
            args = parser.parse_args()
        except Exception:
            UserSessionsResponseGet = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(UserSessionsResponseGet,
                                          HTTPStatus.BAD_REQUEST)

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

        try:
            existingUser = authServer.db.users.find_one({"username": username})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):

                try:
                    AllUserSessions = \
                        authServer.db.sessions.\
                        find({"username": username}).\
                        skip(query_start).\
                        limit(query_limit)
                    AllUserSessionsCount = \
                        authServer.db.sessions.\
                        count_documents({"username": username})
                except Exception as e:
                    return helpers.handleDatabasebError(e)

                # Calculo de las URL hacia anterior y siguiente
                start_previous = query_start - query_limit
                start_next = query_start + query_limit
                if (start_previous < 0
                   or (start_previous >= AllUserSessionsCount)
                   or (query_start == 0 and query_limit == 0)
                   or (query_limit == 0)):
                    url_previous = None
                else:
                    url_previous = request.path +\
                                "?start=" +\
                                str(start_previous) +\
                                "&limit=" +\
                                str(query_limit)

                if (start_next >= AllUserSessionsCount
                   or (query_start == 0 and query_limit == 0)
                   or (query_limit == 0)):
                    url_next = None
                else:
                    url_next = request.path +\
                            "?start=" +\
                            str(start_next) +\
                            "&limit=" +\
                            str(query_limit)

                UserSessionsResultsGet = []
                for existingSession in AllUserSessions:
                    if (datetime.utcnow()
                       <
                       datetime.fromisoformat(existingSession["expires"])):
                        retrievedSession = {
                            "id": str(existingSession["_id"]),
                            "username": existingSession["username"],
                            "session_token": existingSession["session_token"],
                            "expires":  existingSession["expires"],
                            "date_created": existingSession["date_created"]
                        }
                        UserSessionsResultsGet.append(retrievedSession)

                # Construimos la respuesta paginada
                UserSessionsResponseGet = {
                    "total": AllUserSessionsCount,
                    "limit": query_limit,
                    "next": url_next,
                    "previous": url_previous,
                    "results": UserSessionsResultsGet
                }

                return helpers.return_request(UserSessionsResponseGet,
                                              HTTPStatus.OK)

            UserSessionsGet = {
                "code": -1,
                "message": "User '" + username + "' account is closed.",
                "data:": None
            }
            return helpers.return_request(UserSessionsGet,
                                          HTTPStatus.BAD_REQUEST)

        UserSessionsGet = {
            "code": -1,
            "message": "User '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(UserSessionsGet, HTTPStatus.NOT_FOUND)

    # verbo DELETE - cerrar todas las sesiones del usuario
    @helpers.require_apikey
    @helpers.log_reqId
    def delete(self, username):
        # Pasamos el usuario que viene en el path a minusculas
        username = str.lower(username)

        authServer.app.logger.info(helpers.log_request_id() +
                                   "All sessions deletion for user '" +
                                   username +
                                   "' requested.")

        try:
            existingSession = authServer.db.sessions.find_one({
                "username": username
            })
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingSession is not None):

            try:
                authServer.db.sessions.delete_many({
                    "username": username
                })
            except Exception as e:
                return helpers.handleDatabasebError(e)

            SessionResponseDelete = {
                "code": 0,
                "message": "All sessions for user '" +
                           username +
                           "' deleted.",
                "data": None
            }
            return helpers.return_request(SessionResponseDelete, HTTPStatus.OK)

        SessionResponseDelete = {
            "code": -1,
            "message": "No sessions for user '" +
                       username +
                       "' were found.",
            "data": None
        }
        return helpers.return_request(SessionResponseDelete,
                                      HTTPStatus.NOT_FOUND)
