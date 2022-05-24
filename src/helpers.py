# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
import re
from datetime import datetime
# Flask, para la implementacion del servidor REST
from flask import request
from flask_log_request_id import current_request_id
from http import HTTPStatus
# Wraps, para implementacion de decorators
from functools import wraps

# Importacion del archivo principal
import auth_server as authServer


# Decorator que valida la API key provista en los request headers
def require_apikey(view_function):
    @wraps(view_function)
    def check_apikey_decorated(*args, **kwargs):
        authServer.app.logger.debug(log_request_id() +
                                    "Checking API KEY for client ID: \"" +
                                    str(request.headers.get("X-Client-ID")) +
                                    "\".")
        if request.headers.get("X-Client-ID") \
           and \
           request.headers.get("X-Client-ID") \
           == authServer.api_key:
            authServer.app.logger.debug(log_request_id() + "Authorized.")
            return view_function(*args, **kwargs)
        else:
            ApiResponseUnauthorized = {
                "code": -1,
                "message": "You are not authorized to access this resource.",
                "data": None
            }
            return return_request(ApiResponseUnauthorized,
                                  HTTPStatus.UNAUTHORIZED)
    return check_apikey_decorated


# Decorator que loguea el request ID de los headers como info
def log_reqId(view_function):
    @wraps(view_function)
    def check_and_log_req_id(*args, **kwargs):
        authServer.app.logger.info(log_request_id() +
                                   "Request ID: \"" +
                                   str(current_request_id()) +
                                   "\".")
        return view_function(*args, **kwargs)
    return check_and_log_req_id


# Funcion que limpia la collection de sesiones vencidas
def prune_sessions():
    authServer.app.logger.info("prune_sessions: starting...")
    AllSessions = authServer.db.sessions.find()
    sessionCount = authServer.db.sessions.count_documents({})
    sessionDeleted = 0
    if (sessionCount > 0):
        authServer.app.logger.info("prune_sessions: " +
                                   str(sessionCount) +
                                   " sessions found.")
        for existingSession in AllSessions:
            if (datetime.utcnow()
               >
               datetime.fromisoformat(existingSession["expires"])):
                authServer.db.sessions.delete_one(existingSession)
                sessionDeleted += 1
        authServer.app.logger.info("prune_sessions: deleted " +
                                   str(sessionDeleted) +
                                   " expired sessions.")
    else:
        authServer.app.logger.info("prune_sessions: no sessions found.")
    authServer.app.logger.info("prune_sessions: done.")

    # Armamos el documento a guardar en la base de datos
    pruneSession = {
        "log_type": "task",
        "request_date": datetime.utcnow().isoformat(),
        "task_type": "prune expired sessions",
        "api_version": "v" + authServer.api_version,
        "pruned_sessions": sessionDeleted
    }
    authServer.db.requestlog.insert_one(pruneSession)
    authServer.app.logger.debug('Prune expired sessions:' +
                                ' task data successfully logged to DB.')

    return 0


# Funcion que limpia la collection de recovery vencidas
def prune_recovery():

    authServer.app.logger.info("prune_recovery: starting...")
    AllRecovery = authServer.db.recovery.find()
    recoveryCount = authServer.db.recovery.count_documents({})
    recoveryDeleted = 0
    if (recoveryCount > 0):
        authServer.app.logger.info("prune_recovery: " +
                                   str(recoveryCount) +
                                   " requests found.")
        for existingRecovery in AllRecovery:
            if (datetime.utcnow()
               >
               datetime.fromisoformat(existingRecovery["expires"])):
                authServer.db.recovery.delete_one(existingRecovery)
                recoveryDeleted += 1
        authServer.app.logger.info("prune_recovery: deleted " +
                                   str(recoveryDeleted) +
                                   " expired requests.")
    else:
        authServer.app.logger.info("prune_recovery: no requests found.")
    authServer.app.logger.info("prune_recovery: done.")

    # Armamos el documento a guardar en la base de datos
    pruneLog = {
        "log_type": "task",
        "request_date": datetime.utcnow().isoformat(),
        "task_type": "prune expired recovery requests",
        "api_version": "v" + authServer.api_version,
        "pruned_requests": recoveryDeleted
    }
    authServer.db.requestlog.insert_one(pruneLog)
    authServer.app.logger.debug('Prune expired recovery requests: ' +
                                'task data successfully logged to DB.')

    return 0


# Funcion que devuelve los return de los requests
def return_request(message, status):

    # Loguea el mensaje a responder, y su codigo HTTP
    authServer.app.logger.debug(log_request_id() + str(message))
    authServer.app.logger.info(log_request_id() +
                               "Returned HTTP: " +
                               str(status.value))

    return message, status


# Funcion que devuelve el request id, o None si no aplica
# formateado para el log default de Gunicorn
def log_request_id():
    return "[" + str(current_request_id()) + "] "


# Funcion que chequea si un string esta vacio
def non_empty_string(s):
    if not s:
        raise ValueError("Must not be empty string.")
    return s


# Funcion que chequea si una fecha es valida
def non_empty_date(d):
    try:
        d = datetime.strptime(d, "%Y-%m-%d")
    except Exception:
        raise ValueError("Must be valid date.")
    return d


# Funcion que chequea si un bool es valido
def non_empty_bool(b):
    if (str(b).lower() == "true"):
        return True
    else:
        return False


# Funcion que chequea si un email es valido
def non_empty_email(e):
    if (re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
                 e)
       is None):
        raise ValueError("Must be valid email.")
    return e


# Funcion que chequea si un avatar es valido
def non_empty_avatar(a):
    if (re.match(r"([(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\-\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))",
                 a)
       is None):
        raise ValueError("Must be valid URL.")
    return a
