# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
from datetime import datetime
# Flask, para la implementacion del servidor REST
from flask_restful import Resource, reqparse
from http import HTTPStatus
# Passlib para encriptar contrasenias
from passlib.apps import custom_app_context

# Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers


# Clase que define el endpoint para trabajar con usuarios administradores
# Operaciones CRUD: Create, Read, Update, Delete
# verbo GET - listar usuarios
# verbo POST - nuevo usario
class AllAdminUsers(Resource):
    # verbo GET - listar usuarios administradores
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'All admin users requested.')

        try:
            parser = reqparse.RequestParser()
            parser.add_argument("show_closed", type=helpers.non_empty_string,
                                required=False, nullable=False)
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

        if (show_closed is True):
            allUsers = authServer.db.adminusers.find()
        else:
            allUsers = authServer.db.adminusers.find({"account_closed": False})

        AllUsersResponseGet = []
        for existingUser in allUsers:
            retrievedUser = {
                "id": str(existingUser["_id"]),
                "username": existingUser["username"],
                "first_name": existingUser["first_name"],
                "last_name":  existingUser["last_name"],
                "email": existingUser["email"],
                "account_closed": existingUser["account_closed"],
                "date_created": existingUser["date_created"],
                "date_updated": existingUser["date_updated"]
            }
            AllUsersResponseGet.append(retrievedUser)

        return helpers.return_request(AllUsersResponseGet, HTTPStatus.OK)

    # verbo POST - nuevo usario administrador
    @helpers.require_apikey
    @helpers.log_reqId
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("username", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("password", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("first_name", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("last_name", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("email", type=helpers.non_empty_email,
                                required=True, nullable=False)
            args = parser.parse_args()
        except Exception:
            UserResponsePost = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(UserResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        authServer.app.logger.info(helpers.log_request_id() +
                                   "New adminuser '" +
                                   args["username"] +
                                   "' requested.")

        existingUser = authServer.db.users.find_one(
            {"username": args["username"]})
        existingAdminUser = authServer.db.adminusers.find_one(
            {"username": args["username"]})
        if ((existingUser is not None) or (existingAdminUser is not None)):
            UserResponsePost = {
                "code": -2,
                "message": "Bad request. Admin user '" + args["username"] +
                           "' already exists.",
                "data": None
            }
            return helpers.return_request(UserResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        userToInsert = {
            "username": args["username"],
            "password": custom_app_context.hash(args["password"]),
            "first_name": args["first_name"],
            "last_name": args["last_name"],
            "email": args["email"],
            "account_closed": False,
            "date_created": datetime.utcnow().isoformat(),
            "date_updated": None
        }
        UserResponsePost = userToInsert.copy()
        authServer.db.adminusers.insert_one(userToInsert)
        id_userToInsert = str(userToInsert["_id"])
        UserResponsePost["id"] = id_userToInsert
        UserResponsePost.pop("password", None)

        return helpers.return_request(UserResponsePost, HTTPStatus.CREATED)


# Clase que define el endpoint para trabajar con usuarios administradores
# Operaciones CRUD: Create, Read, Update, Delete
# verbo GET - leer usuario administrador
# verbo PUT - actualizar usuario administrador completo (sin contrasenia)
# verbo PATCH - actualizar contrasenia. solo permite op=replace y path=password
# verbo DELETE - borrar usuario administrador
class AdminUser(Resource):

    # verbo GET - leer usuario administrador
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self, username):
        authServer.app.logger.info(helpers.log_request_id() + "Admin user '" +
                                   username + "' information requested.")

        existingUser = authServer.db.adminusers.find_one(
            {"username": username})
        if (existingUser is not None):
            UserResponseGet = {
                "id": str(existingUser["_id"]),
                "username": existingUser["username"],
                "first_name": existingUser["first_name"],
                "last_name": existingUser["last_name"],
                "email": existingUser["email"],
                "account_closed": existingUser["account_closed"],
                "date_created": existingUser["date_created"],
                "date_updated": existingUser["date_updated"]
            }
            return helpers.return_request(UserResponseGet, HTTPStatus.OK)

        UserResponseGet = {
            "code": -1,
            "message": "Admin user '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(UserResponseGet, HTTPStatus.NOT_FOUND)

    # verbo PUT - actualizar usuario completo, si no existe lo crea
    @helpers.require_apikey
    @helpers.log_reqId
    def put(self, username):
        authServer.app.logger.info(helpers.log_request_id() + "Admin user '" +
                                   username + "' update requested.")

        try:
            parser = reqparse.RequestParser()
            parser.add_argument("first_name", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("last_name", type=helpers.non_empty_string,
                                required=True, nullable=False)
            parser.add_argument("email", type=helpers.non_empty_email,
                                required=True, nullable=False)
            args = parser.parse_args()
        except Exception:
            UserResponsePut = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(UserResponsePut,
                                          HTTPStatus.BAD_REQUEST)

        existingUser = authServer.db.adminusers.find_one(
            {"username": username})
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):

                userToUpdate = {
                    "first_name": args["first_name"],
                    "last_name": args["last_name"],
                    "email": args["email"],
                    "account_closed": existingUser["account_closed"],
                    "date_created": existingUser["date_created"],
                    "date_updated": datetime.utcnow().isoformat()
                }

                UserResponsePut = userToUpdate.copy()
                authServer.db.adminusers.update_one(
                    {"username": username}, {'$set': userToUpdate})
                id_userToUpdate = str(existingUser["_id"])
                UserResponsePut["username"] = existingUser["username"]
                UserResponsePut["id"] = id_userToUpdate

                return helpers.return_request(UserResponsePut, HTTPStatus.OK)

            UserResponsePut = {
                "code": -2,
                "message": "Admin user '" + username + "' account is closed.",
                "data:": None
            }
            return helpers.return_request(UserResponsePut,
                                          HTTPStatus.BAD_REQUEST)

        UserResponsePut = {
            "code": -1,
            "message": "Admin user '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(UserResponsePut, HTTPStatus.NOT_FOUND)

    # verbo PATCH - actualizar contrasenia.
    # solo permite op=replace y path=password
    # { "op": "replace", "path": "/password", "value": "" }
    @helpers.require_apikey
    @helpers.log_reqId
    def patch(self, username):
        authServer.app.logger.info(helpers.log_request_id() +
                                   "Password modification for admin user '" +
                                   username + "' requested.")
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("op", type=helpers.non_empty_string,
                                required=True, nullable=False,
                                choices=['replace'])
            parser.add_argument("path", type=helpers.non_empty_string,
                                required=True, nullable=False,
                                choices=['/password'])
            parser.add_argument("value", type=helpers.non_empty_string,
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

        existingUser = authServer.db.adminusers.find_one(
            {"username": username})
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):

                existingUser["password"] = custom_app_context.hash(
                    args["value"])
                existingUser["date_updated"] = datetime.utcnow().isoformat()
                authServer.db.adminusers.update_one(
                    {"username": username}, {'$set': existingUser})

                userResponsePatch = {
                    "code": 0,
                    "message": "Admin user '" + username +
                               "' password updated.",
                    "data:": None
                }
                return helpers.return_request(userResponsePatch, HTTPStatus.OK)

            userResponsePatch = {
                "code": -2,
                "message": "Admin user '" + username + "' account is closed.",
                "data:": None
            }
            return helpers.return_request(userResponsePatch,
                                          HTTPStatus.BAD_REQUEST)

        userResponsePatch = {
            "code": -1,
            "message": "Admin user '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(userResponsePatch, HTTPStatus.NOT_FOUND)

    # verbo DELETE - borrar usuario administrador
    @helpers.require_apikey
    @helpers.log_reqId
    def delete(self, username):
        authServer.app.logger.info(helpers.log_request_id() + "Admin user '" +
                                   username + "' close account requested.")

        existingUser = authServer.db.adminusers.find_one(
            {"username": username})
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):

                authServer.db.adminusers.update_one(
                    {"username": username},
                    {'$set':
                        {'account_closed': True,
                         'date_updated': datetime.utcnow().isoformat()}})
                authServer.db.sessions.delete_many({"username": username})

                UserResponseDelete = {
                    "code": 0,
                    "message": "Admin user '" + username +
                               "' marked as closed account.",
                    "data": None
                }
                return helpers.return_request(UserResponseDelete,
                                              HTTPStatus.OK)

            UserResponseDelete = {
                "code": -1,
                "message": "Admin user '" + username +
                           "' account is already closed.",
                "data": None
            }
            return helpers.return_request(UserResponseDelete,
                                          HTTPStatus.BAD_REQUEST)

        UserResponseDelete = {
            "code": -1,
            "message": "Admin user '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(UserResponseDelete, HTTPStatus.NOT_FOUND)


# Clase que define el endpoint para obtener las sesiones de un usuario admin
# verbo GET - obtener sesiones vigentes del usuario admin
class AdminUserSessions(Resource):

    # verbo GET - obtener sesiones vigentes del usuario admin
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self, username):
        authServer.app.logger.info(helpers.log_request_id() + "Admin user '" +
                                   username + "' sessions requested.")

        existingUser = authServer.db.adminusers.find_one(
            {"username": username})
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):

                UserSessionsResponseGet = []
                AllUserSessions = authServer.db.sessions.find(
                    {"username": username})
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
                        UserSessionsResponseGet.append(retrievedSession)
                return helpers.return_request(UserSessionsResponseGet,
                                              HTTPStatus.OK)

            UserSessionsGet = {
                "code": -1,
                "message": "Admin user '" + username + "' account is closed.",
                "data:": None
            }
            return helpers.return_request(UserSessionsGet,
                                          HTTPStatus.BAD_REQUEST)

        UserSessionsGet = {
            "code": -1,
            "message": "Admin user '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(UserSessionsGet, HTTPStatus.NOT_FOUND)
