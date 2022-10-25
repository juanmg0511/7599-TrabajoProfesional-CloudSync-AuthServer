# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# src/stats.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
import time
import sys
from datetime import date, datetime
# Flask, para la implementacion del servidor REST
from flask import g, request, json
from flask_restful import Resource, reqparse
from http import HTTPStatus
from bson import json_util

# Importacion de las configuracion del Auth Server
import auth_server_config as config
# Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers


# Funcion que actualiza en la base de datos las estadisticas del dia
def update_stats(response):
    authServer.app.logger.debug(helpers.log_request_id() +
                                'Updating daily stats data in DB.')

    # Escapeamos paths que no son de la api
    if (not(config.api_path in request.path)):
        authServer.app.logger.debug(helpers.log_request_id() +
                                    'Request is not from API path, skipping.')
        return response

    # Buscamos el registro de stats en la base de datos
    try:
        today_stats = authServer.\
                      db_log.\
                      stats.\
                      find_one({"date": {"$regex": str(date.today())}})
    except Exception as e:
        return helpers.handleLogDatabasebError(e)

    # Por default, vamos a asumir que no existe y que hay que
    # crearlo
    new_record = True
    if today_stats is not None:
        new_record = False

    # Inicializacion de variables para los calculos
    # Calculos sobre requests
    requests_number = 0 if new_record is True \
        else today_stats["requests_number"]
    requests_users = 0 if new_record is True \
        else today_stats["requests_users"]
    requests_adminusers = 0 if new_record is True \
        else today_stats["requests_adminusers"]
    requests_sessions = 0 if new_record is True \
        else today_stats["requests_sessions"]
    requests_recovery = 0 if new_record is True \
        else today_stats["requests_recovery"]
    requests_error_400 = 0 if new_record is True \
        else today_stats["requests_error_400"]
    requests_error_401 = 0 if new_record is True \
        else today_stats["requests_error_401"]
    requests_error_404 = 0 if new_record is True \
        else today_stats["requests_error_404"]
    requests_error_405 = 0 if new_record is True \
        else today_stats["requests_error_405"]
    requests_error_500 = 0 if new_record is True \
        else today_stats["requests_error_500"]
    requests_error_503 = 0 if new_record is True \
        else today_stats["requests_error_503"]
    # Calculos sobre requests
    response_time_max = 0 if new_record is True \
        else today_stats["response_time_max"]
    response_time_min = sys.float_info.max if new_record is True \
        else today_stats["response_time_min"]
    response_time_avg = 0
    # Calculos sobre usuarios
    users_post = 0 if new_record is True \
        else today_stats["users_new"]
    users_delete = 0 if new_record is True \
        else today_stats["users_deleted"]
    sessions_post = 0 if new_record is True \
        else today_stats["sessions_opened"]
    sessions_delete = 0 if new_record is True \
        else today_stats["sessions_closed"]
    recovery_post = 0 if new_record is True \
        else today_stats["recovery_requests"]

    # Calculos y formatos de la informacion
    requests_number += 1

    now = time.time()
    duration = round(now - g.start, 6)

    if (duration < response_time_min):
        response_time_min = duration
    if (duration > response_time_max):
        response_time_max = duration
    response_time_avg = (response_time_min + response_time_max) / 2

    if ("/users" in request.path):
        requests_users += 1
        if (("POST" in request.method) and (str(HTTPStatus.CREATED.value)
           in str(response.status))):
            users_post += 1
        if (("DELETE" in request.method)
           and (str(HTTPStatus.OK.value) in str(response.status))):
            users_delete += 1

    if ("/adminusers" in request.path):
        requests_adminusers += 1

    if ("/sessions" in request.path):
        requests_sessions += 1
        if (("POST" in request.method) and (str(HTTPStatus.CREATED.value)
           in str(response.status))):
            sessions_post += 1
        if ("DELETE" in request.method
           and (str(HTTPStatus.OK.value) in str(response.status))):
            sessions_delete += 1

    if ("/recovery" in request.path):
        requests_recovery += 1
        if (("POST" in request.method) and (str(HTTPStatus.CREATED.value)
           in str(response.status))):
            recovery_post += 1

    if (str(HTTPStatus.BAD_REQUEST.value)
       in str(response.status)):
        requests_error_400 += 1

    if (str(HTTPStatus.UNAUTHORIZED.value)
       in str(response.status)):
        requests_error_401 += 1

    if (str(HTTPStatus.NOT_FOUND.value)
       in str(response.status)):
        requests_error_404 += 1

    if (str(HTTPStatus.METHOD_NOT_ALLOWED.value)
       in str(response.status)):
        requests_error_405 += 1

    if (str(HTTPStatus.INTERNAL_SERVER_ERROR.value)
       in str(response.status)):
        requests_error_500 += 1

    if (str(HTTPStatus.SERVICE_UNAVAILABLE.value)
       in str(response.status)):
        requests_error_503 += 1

    # Registro a crear/actualizar en la DB, para cada dia
    stat = {
        # fecha
        "date": str(date.today()) if new_record is True \
        else today_stats["date"],
        # cant requests en el dia
        "requests_number": requests_number,
        # hits endpoint users
        # hits endpoint adminusers
        # hits endpoint sessions
        # hits endpoint recovery
        # requests por minuto para el dia (parcial hasta el ultimo update)
        "requests_users": requests_users,
        "requests_adminusers": requests_adminusers,
        "requests_sessions": requests_sessions,
        "requests_recovery": requests_recovery,
        "requests_per_minute": requests_number/1440,
        # tiempo de respuesta maximo
        # tiempo de respuesta minimo
        # tiempo de respuesta promedio
        "response_time_max": response_time_max,
        "response_time_min": response_time_min,
        "response_time_avg": response_time_avg,
        # cantidad de usuarios nuevos
        # cantidad de usuario dados de baja
        # cantidad de sesiones abiertas
        # cantidad de sesiones cerradas
        # cantidad recovery abiertos
        "users_new": users_post,
        "users_deleted": users_delete,
        "sessions_opened": sessions_post,
        "sessions_closed": sessions_delete,
        "recovery_requests": recovery_post,
        # errores 40X y 50X
        "requests_error_400": requests_error_400,
        "requests_error_401": requests_error_401,
        "requests_error_404": requests_error_404,
        "requests_error_405": requests_error_405,
        "requests_error_500": requests_error_500,
        "requests_error_503": requests_error_503
    }

    # Insertamos o actualizamos el registro en la base de datos
    try:
        if new_record is True:
            authServer.db_log.stats.insert_one(
                stat)
        else:
            authServer.db_log.stats.update_one(
                {"date": stat["date"]}, {'$set': stat})
    except Exception as e:
        return helpers.handleLogDatabasebError(e)

    authServer.app.logger.debug(helpers.log_request_id() +
                                'Daily stats data successfully updated in DB.')

    return response


# Clase que entrega estadisticas del uso del servidor
class Stats(Resource):

    # verbo GET - obtener registros de estadisticas
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'Server stats requested.')
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("sortascending", type=helpers.non_empty_string,
                                required=False, nullable=True)
            args = parser.parse_args()

        except Exception:
            statsResponseGet = {
                "code": -1,
                "message": "Bad request. Missing or wrong format for " +
                           "required arguments.",
                "data": None
            }
            return helpers.return_request(statsResponseGet,
                                          HTTPStatus.BAD_REQUEST)

        sort_ascending = str(args.get("sortascending", "False"))
        if (str(sort_ascending).
           lower().
           replace("\"", "").
           replace("'", "") == "true"):
            sort_ascending = 1
        else:
            sort_ascending = -1

        authServer.app.logger.debug(helpers.log_request_id() +
                                    "Sort ascending: " +
                                    str(sort_ascending))

        # Respuesta de estadisticas, incluye estadisticas generales
        # y la lista de dias
        try:
            # Obtenemos los registros de estadisticas
            dailyStats = authServer.db_log.stats.\
                find({}).\
                skip(0).\
                limit(config.stats_days_to_keep).\
                sort("date", sort_ascending)
            dailyStatsDict = [doc for doc in dailyStats]
            dailyStatsDictJson = json.\
                dumps(dailyStatsDict, default=json_util.default)
            dailyStatsArray = json.loads(dailyStatsDictJson)

            # Construimos la respuesta a devolver
            statsResponseGet = {
                "request_date:":
                datetime.utcnow().isoformat(),
                "registered_users":
                authServer.db.users.
                count_documents({}),
                "registered_users_login_service":
                authServer.db.users.
                count_documents({"login_service": True}),
                "registered_users_active":
                authServer.db.users.
                count_documents({"account_closed": False}),
                "registered_users_closed":
                authServer.db.users.
                count_documents({"account_closed": True}),
                "registered_adminusers":
                authServer.db.adminusers.
                count_documents({}),
                "registered_adminusers_active":
                authServer.db.adminusers.
                count_documents({"account_closed": False}),
                "registered_adminusers_closed":
                authServer.db.adminusers.
                count_documents({"account_closed": True}),
                "active_sessions":
                authServer.db.sessions.
                count_documents({}),
                "active_recovery":
                authServer.db.recovery.
                count_documents({}),
                "daily_stats":
                dailyStatsArray
            }
        except Exception as e:
            return helpers.handleDatabasebError(e)

        return helpers.return_request(statsResponseGet, HTTPStatus.OK)
