# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# src/recovery.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
import uuid
from datetime import datetime, timedelta
# Flask, para la implementacion del servidor REST
from flask_restful import Resource, reqparse
from http import HTTPStatus
# Passlib para encriptar contrasenias
from passlib.apps import custom_app_context

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
        AllRecoveryResponseGet = []
        AllRecoveries = authServer.db.recovery.find()

        for existingRecovery in AllRecoveries:
            retrievedRecovery = {
                "id": str(existingRecovery["_id"]),
                "username": existingRecovery["username"],
                "recovery_key": existingRecovery["recovery_key"],
                "expires":  existingRecovery["expires"],
                "date_created": existingRecovery["date_created"]
            }
            AllRecoveryResponseGet.append(retrievedRecovery)

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
                                   args["username"] + "' requested.")

        existingUser = authServer.db.users.find_one(
                            {"username": args["username"]})
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):
                if (existingUser["login_service"] is False):
                    existingRecovery = authServer.db.recovery.find_one(
                                        {"username": args["username"]})
                    if (existingRecovery is not None):
                        authServer.db.recovery.delete_one(
                                        {"username": args["username"]})

                    recoveryToInsert = {
                        "username": args["username"],
                        "recovery_key": str(uuid.uuid1()),
                        "expires": (datetime.utcnow() +
                                    timedelta(
                                        minutes=int(
                                            authServer.recovery_length
                                        )
                                    )).isoformat(),
                        "date_created": datetime.utcnow().isoformat()
                    }
                    RecoveryResponsePost = recoveryToInsert.copy()
                    authServer.db.recovery.insert_one(recoveryToInsert)
                    id_recoveryToInsert = str(recoveryToInsert["_id"])
                    RecoveryResponsePost["id"] = id_recoveryToInsert

                    helpers.send_recovery_notification(
                        user=existingUser,
                        recovery_key=RecoveryResponsePost["recovery_key"])
                    return helpers.return_request(RecoveryResponsePost,
                                                  HTTPStatus.CREATED)

                RecoveryResponsePost = {
                   "code": -3,
                   "message": "User '" + args["username"] +
                              "' uses a login service, " +
                              "can't recover password.",
                   "data:": None
                }
                return helpers.return_request(RecoveryResponsePost,
                                              HTTPStatus.BAD_REQUEST)

            RecoveryResponsePost = {
                    "code": -2,
                    "message": "Bad request. Account '" +
                               args["username"] +
                               "' is closed.",
                    "data": None
            }
            return helpers.return_request(RecoveryResponsePost,
                                          HTTPStatus.BAD_REQUEST)

        RecoveryResponsePost = {
            "code": -1,
            "message": "User '" + args["username"] + "' not found.",
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
        authServer.app.logger.info(helpers.log_request_id() +
                                   "Password recovery request for username '"
                                   + username +
                                   "' requested.")

        existingUser = authServer.db.users.find_one({"username": username})
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):
                if (existingUser["login_service"] is False):
                    existingRecovery = authServer.db.recovery.find_one(
                                        {"username": username})
                    if (existingRecovery is not None):
                        if (datetime.utcnow()
                           <
                           datetime.fromisoformat(
                              existingRecovery["expires"])):
                            RecoveryResponsePost = {
                              "id": str(existingRecovery["_id"]),
                              "username": existingRecovery["username"],
                              "recovery_key": existingRecovery["recovery_key"],
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

        existingUser = authServer.db.users.find_one({"username": username})
        if (existingUser is not None):
            if (existingUser["account_closed"] is False):
                if (existingUser["login_service"] is False):
                    existingRecovery = \
                        authServer.db.recovery.find_one({"username": username})
                    if (existingRecovery is not None):
                        if (datetime.utcnow()
                           <
                           datetime.fromisoformat(
                               existingRecovery["expires"])):
                            if (args["recovery_key"]
                               ==
                               existingRecovery["recovery_key"]):

                                # Cambia la password
                                existingUser["password"] = \
                                    custom_app_context.hash(
                                        args["new_password"])
                                existingUser["date_updated"] = \
                                    datetime.utcnow().isoformat()
                                authServer.db.users.update_one(
                                                     {"username": username},
                                                     {'$set': existingUser})

                                # Cambiada la password, se borra el request
                                authServer.db.recovery.delete_one(
                                                        {"username": username})

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
