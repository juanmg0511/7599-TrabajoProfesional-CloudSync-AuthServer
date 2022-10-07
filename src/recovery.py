# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# src/recovery.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
from datetime import datetime, timedelta
# Flask, para la implementacion del servidor REST
from flask_restful import Resource, reqparse
from flask import request
from http import HTTPStatus
# Flask-JWT-Extended para la generacion de recovery keys
from flask_jwt_extended import create_access_token
from flask_jwt_extended import decode_token
# Passlib para encriptar contrasenias
from passlib.apps import custom_app_context

# Importacion de las configuracion del Auth Server
import auth_server_config as config
# Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers


# Clases que permiten realizar la recuperacion de contraseña
# SOLO PARA USUARIOS DE LA APP
# verbo GET - recuperar todos los pedidos de recupero de contraseña
# verbo POST - crear pedido de recupero de contraseña, si ya existe uno lo
# pisa y lo regenera
class AllRecovery(Resource):
    # verbo GET - recuperar todos los pedidos de recupero de contraseña
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'All password recovery requests requested.')

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
                                type=helpers.non_empty_and_safe_username,
                                required=False,
                                nullable=False)
            args = parser.parse_args()
        except Exception:
            AllRecoveryResponseGet = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(AllRecoveryResponseGet,
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

        # Operacion de base de datos
        try:
            AllRecoveries = authServer.db.recovery.\
                            find(find_query).\
                            skip(query_start).\
                            limit(query_limit)
            AllRecoveriesCount = authServer.db.recovery.\
                count_documents(find_query)
        except Exception as e:
            return helpers.handleDatabasebError(e)

        # Calculo de las URL hacia anterior y siguiente
        start_previous = query_start - query_limit
        start_next = query_start + query_limit
        if (start_previous < 0
           or (start_previous >= AllRecoveriesCount)
           or (query_start == 0 and query_limit == 0)
           or (query_limit == 0)):
            url_previous = None
        else:
            url_previous = request.path +\
                           "?start=" +\
                           str(start_previous) +\
                           "&limit=" +\
                           str(query_limit)

        if (start_next >= AllRecoveriesCount
           or (query_start == 0 and query_limit == 0)
           or (query_limit == 0)):
            url_next = None
        else:
            url_next = request.path +\
                       "?start=" +\
                       str(start_next) +\
                       "&limit=" +\
                       str(query_limit)

        AllRecoveryResultsGet = []
        for existingRecovery in AllRecoveries:
            retrievedRecovery = {
                "id": str(existingRecovery["_id"]),
                "username": existingRecovery["username"],
                "email": existingRecovery["email"],
                "recovery_key": existingRecovery["recovery_key"],
                "expired":  (datetime.utcnow() > datetime.
                             fromisoformat(existingRecovery["expires"])),
                "expires":  existingRecovery["expires"],
                "date_created": existingRecovery["date_created"]
            }
            AllRecoveryResultsGet.append(retrievedRecovery)

        # Construimos la respuesta paginada
        AllRecoveryResponseGet = {
            "total": AllRecoveriesCount,
            "limit": query_limit,
            "next": url_next,
            "previous": url_previous,
            "results": AllRecoveryResultsGet
        }

        return helpers.return_request(AllRecoveryResponseGet, HTTPStatus.OK)

    # verbo POST - crear pedido de recupero de contraseña, si ya existe uno lo
    # pisa y lo regenera
    @helpers.require_apikey
    @helpers.log_reqId
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("username", type=helpers.non_empty_string,
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
                                   "New password recovery request for user '" +
                                   str.lower(args["username"]) +
                                   "' requested.")

        try:
            existingUser = authServer.db.users.find_one(
                                {"username": str.lower(args["username"])})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):
                if (existingUser["login_service"] is False):
                    try:
                        existingRecovery = authServer.db.recovery.find_one(
                                            {"username":
                                                str.lower(args["username"])})
                        if (existingRecovery is not None):
                            authServer.db.recovery.delete_one(
                                            {"username":
                                                str.lower(args["username"])})
                    except Exception as e:
                        return helpers.handleDatabasebError(e)

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

                    recoveryToInsert = {
                        "username": str.lower(args["username"]),
                        "email": existingUser["contact"]["email"],
                        "recovery_key": token,
                        "expires": (datetime.utcnow() +
                                    timedelta(
                                        minutes=int(
                                            config.recovery_length
                                        )
                                    )).isoformat(),
                        "date_created": datetime.utcnow().isoformat()
                    }
                    RecoveryResponsePost = recoveryToInsert.copy()
                    try:
                        authServer.db.recovery.insert_one(recoveryToInsert)
                    except Exception as e:
                        return helpers.handleDatabasebError(e)
                    id_recoveryToInsert = str(recoveryToInsert["_id"])
                    RecoveryResponsePost["id"] = id_recoveryToInsert

                    helpers.send_recovery_notification(
                        user=existingUser,
                        recovery_key=RecoveryResponsePost["recovery_key"])
                    return helpers.return_request(RecoveryResponsePost,
                                                  HTTPStatus.CREATED)

                RecoveryResponsePost = {
                   "code": -3,
                   "message": "User '" + str.lower(args["username"]) +
                              "' uses a login service, " +
                              "can't recover password.",
                   "data:": None
                }
                return helpers.return_request(RecoveryResponsePost,
                                              HTTPStatus.BAD_REQUEST)

            RecoveryResponsePost = {
                    "code": -2,
                    "message": "Bad request. Account '" +
                               str.lower(args["username"]) +
                               "' is closed.",
                    "data": None
            }
            return helpers.return_request(RecoveryResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        RecoveryResponsePost = {
            "code": -1,
            "message": "User '" + str.lower(args["username"]) + "' not found.",
            "data": None
        }
        return helpers.return_request(RecoveryResponsePost,
                                      HTTPStatus.NOT_FOUND)


# Clases que permiten realizar la recuperacion de contraseña
# SOLO PARA USUARIOS DE LA APP
# verbo GET - recuperar un pedido especifico de recupero de contraseña
# verbo POST - cambia la password del usuario, y borra el pedido de
# recuperacion de contraseña, si los datos coinciden
class Recovery(Resource):
    # verbo GET - recuperar un pedido especifico de recupero de contraseña
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self, username):

        # Pasamos el usuario que viene en el path a minusculas
        username = str.lower(username)
        authServer.app.logger.info(helpers.log_request_id() +
                                   "Password recovery request for username '"
                                   + username +
                                   "' requested.")

        try:
            existingUser = authServer.db.users.find_one({"username": username})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):
                if (existingUser["login_service"] is False):
                    try:
                        existingRecovery = authServer.db.recovery.find_one(
                                            {"username": username})
                    except Exception as e:
                        return helpers.handleDatabasebError(e)
                    if (existingRecovery is not None):
                        if (datetime.utcnow()
                           <
                           datetime.fromisoformat(
                              existingRecovery["expires"])):
                            RecoveryResponsePost = {
                              "id": str(existingRecovery["_id"]),
                              "username": existingRecovery["username"],
                              "email": existingRecovery["email"],
                              "recovery_key": existingRecovery["recovery_key"],
                              "expired": (datetime.utcnow() >
                                          datetime.fromisoformat(
                                            existingRecovery["expires"])),
                              "expires":  existingRecovery["expires"],
                              "date_created": existingRecovery["date_created"]
                            }
                            return helpers.return_request(RecoveryResponsePost,
                                                          HTTPStatus.OK)

                        RecoveryResponseGet = {
                            "code": -2,
                            "message": "Recovery request for user '" +
                                       username +
                                       "' has expired.",
                            "data": None
                        }
                        return helpers.return_request(RecoveryResponseGet,
                                                      HTTPStatus.UNAUTHORIZED)

                    RecoveryResponseGet = {
                        "code": -3,
                        "message": "User '" +
                                   username +
                                   "' has not requested password recovery.",
                        "data": None
                    }
                    return helpers.return_request(RecoveryResponseGet,
                                                  HTTPStatus.UNAUTHORIZED)

                RecoveryResponseGet = {
                   "code": -2,
                   "message": "User '" +
                              username +
                              "' uses a login service, " +
                              "can't recover password.",
                   "data:": None
                }
                return helpers.return_request(RecoveryResponseGet,
                                              HTTPStatus.BAD_REQUEST)

            RecoveryResponseGet = {
                "code": -1,
                "message": "User '" + username + "' account is closed.",
                "data:": None
            }
            return helpers.return_request(RecoveryResponseGet,
                                          HTTPStatus.BAD_REQUEST)

        RecoveryResponseGet = {
            "code": -1,
            "message": "User '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(RecoveryResponseGet,
                                      HTTPStatus.NOT_FOUND)

    # verbo POST - cambia la password del usuario, y borra el pedido de
    # recuperacion de contraseña, si los datos coinciden
    @helpers.require_apikey
    @helpers.log_reqId
    def post(self, username):

        # Pasamos el usuario que viene en el path a minusculas
        username = str.lower(username)
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("recovery_key",
                                type=helpers.non_empty_string,
                                required=True,
                                nullable=False)
            parser.add_argument("new_password",
                                type=helpers.non_empty_string,
                                required=True,
                                nullable=False)
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
                                   "New password (recovery) for user '" +
                                   username +
                                   "' requested.")

        try:
            existingUser = authServer.db.users.find_one({"username": username})
        except Exception as e:
            return helpers.handleDatabasebError(e)
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):
                if (existingUser["login_service"] is False):
                    try:
                        existingRecovery = \
                            authServer.db.recovery.find_one(
                                {"username": username})
                    except Exception as e:
                        return helpers.handleDatabasebError(e)

                    if (existingRecovery is not None):
                        try:
                            # Chequeamos si el token suministrado es valido
                            key_data = decode_token(args["recovery_key"])

                            # Vemos si el usuario coincide con el de la sesion
                            if (key_data["identity"]
                               !=
                               existingRecovery["username"]):
                                raise(Exception)
                        except Exception:
                            SessionResponseGet = {
                                "code": -1,
                                "message": "Invalid recovery key '" +
                                           args["recovery_key"] +
                                           "' supplied.",
                                "data": None
                            }
                            return helpers.return_request(
                                SessionResponseGet,
                                HTTPStatus.UNAUTHORIZED)

                        if (datetime.utcnow()
                           <
                           datetime.fromisoformat(
                               existingRecovery["expires"])):
                            if (args["recovery_key"]
                               ==
                               existingRecovery["recovery_key"]):

                                # Cambia la password
                                try:
                                    existingUser["password"] = \
                                        custom_app_context.\
                                        hash(
                                            helpers.
                                            non_empty_and_valid_password(
                                                args["new_password"]))
                                except Exception:
                                    userResponsePatch = {
                                        "code": -1,
                                        "message": "Invalid password.",
                                        "data:": None
                                    }
                                    return helpers.\
                                        return_request(userResponsePatch,
                                                       HTTPStatus.BAD_REQUEST)

                                existingUser["date_updated"] = \
                                    datetime.utcnow().isoformat()
                                try:
                                    authServer.db.users.update_one(
                                                        {"username": username},
                                                        {'$set': existingUser})

                                    # Cambiada la password, se borra el request
                                    authServer.db.recovery.delete_one(
                                        {"username": username})
                                except Exception as e:
                                    return helpers.handleDatabasebError(e)

                                RecoveryResponsePost = {
                                    "code": 0,
                                    "message": "Password for user '" +
                                               username +
                                               "' has been reset.",
                                    "data": None
                                }
                                return helpers.return_request(
                                                RecoveryResponsePost,
                                                HTTPStatus.OK)

                            RecoveryResponsePost = {
                                "code": -4,
                                "message": "Recovery key for user '" +
                                           username +
                                           "' is invalid.",
                                "data": None
                            }
                            return helpers.return_request(
                                            RecoveryResponsePost,
                                            HTTPStatus.UNAUTHORIZED)

                        RecoveryResponsePost = {
                            "code": -2,
                            "message": "Recovery request for user '" +
                                       username +
                                       "' has expired.",
                            "data": None
                        }
                        return helpers.return_request(RecoveryResponsePost,
                                                      HTTPStatus.UNAUTHORIZED)

                    RecoveryResponsePost = {
                        "code": -3,
                        "message": "User '" +
                                   username +
                                   "' has not requested password recovery.",
                        "data": None
                    }
                    return helpers.return_request(RecoveryResponsePost,
                                                  HTTPStatus.UNAUTHORIZED)

                RecoveryResponsePost = {
                    "code": -3,
                    "message": "User '" +
                               username +
                               "' uses a login service, " +
                               "can't recover password.",
                    "data:": None
                }
                return helpers.return_request(RecoveryResponsePost,
                                              HTTPStatus.BAD_REQUEST)

            RecoveryResponsePost = {
                "code": -2,
                "message": "User '" + username + "' account is closed.",
                "data:": None
            }
            return helpers.return_request(RecoveryResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        RecoveryResponsePost = {
            "code": -1,
            "message": "User '" + username + "' not found.",
            "data": None
        }
        return helpers.return_request(RecoveryResponsePost,
                                      HTTPStatus.NOT_FOUND)
