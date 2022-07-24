# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# auth_server.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
import os
import logging
import atexit
# Flask, para la implementacion del servidor REST
from flask import Flask
from flask_restful import Api
from flask_log_request_id import RequestID
from flask_cors import CORS
# Flask-sendmail para el envio de correo
from flask_mail import Mail
# PyMongo para el manejo de MongoDB
from flask_pymongo import PyMongo
# Flask-JWT-Extended para la generacion de tokens
from flask_jwt_extended import JWTManager
# Flask-APScheduler para el prune de la collection de sesiones
from apscheduler.schedulers.background import BackgroundScheduler
# Flask-Talisman para el manejo de SSL
from flask_talisman import Talisman

# Importacion de clases necesarias
from src import home, adminusers, users, sessions, recovery, \
                requestlog, helpers

# Version de API y Server
api_version = "1"
server_version = "1.00"

# Valores default
# Solo para ejecutar en forma directa!
app_debug_default = True
app_port_default = 8000

# Para todos los modos
app_env_default = "DEV"
api_key_default = "44dd22ca-836d-40b6-aa49-7981ded03667"
session_length_minutes_default_user = 60
session_length_minutes_default_admin = 30
recovery_length_minutes_default = 2880
prune_interval_sessions_seconds_default = 3600
prune_interval_recovery_seconds_default = 86400
sendmail_active_default = "1"
sendmail_server_default = "auth-server-mailhog"
sendmail_from_default = "do-not-reply@cloudsync.com"
sendmail_port_default = 1025
sendmail_username_default = None
sendmail_password_default = None
sendmail_tls_default = "0"
sendmail_ssl_default = "0"
sendmail_base_url_default = "http://127.0.0.1"
username_max_length_default = 64
password_policy_default = {
    "min": 5,
    "max": 256,
    "digits": False,
    "letters": False,
    "lowercase": False,
    "uppercase": False,
    "symbols": False
}
avatar_max_width_default = 256
avatar_max_height_default = 256
avatar_max_size_default = 524288
google_client_id_default = None
mongodb_hostname_default = "127.0.0.1"
mongodb_database_default = "auth-server-db:27017"
mongodb_username_default = "authserveruser"
mongodb_password_default = "*"
mongodb_ssl_default = "false"
mongodb_replica_set_default = "None"
mongodb_auth_source_default = "None"
jwt_secret_default = "super-secret"

# Agregamos un root para todos los enpoints, con la api version
api_path = "/api/v" + api_version

# Inicializacion de la api
app = Flask(__name__)
api = Api(app)
# Inicializacion del sistema de correo
mail_active = os.environ.get("SENDMAIL_ACTIVE",
                             sendmail_active_default)
app.config["MAIL_SERVER"] = os.environ.get("SENDMAIL_SERVER",
                                           sendmail_server_default)
app.config["MAIL_PORT"] = os.environ.get("SENDMAIL_PORT",
                                         sendmail_port_default)
app.config["MAIL_USERNAME"] = os.environ.get("SENDMAIL_USERNAME",
                                             sendmail_username_default)
app.config["MAIL_PASSWORD"] = os.environ.get("SENDMAIL_PASSWORD",
                                             sendmail_password_default)
if (os.environ.get("SENDMAIL_ACTIVE", sendmail_tls_default) == "1"):
    mail_active = True
else:
    mail_active = False
if (os.environ.get("SENDMAIL_USE_TLS", sendmail_tls_default) == "1"):
    app.config["MAIL_USE_TLS"] = True
else:
    app.config["MAIL_USE_TLS"] = False
if (os.environ.get("SENDMAIL_USE_SSL", sendmail_ssl_default) == "1"):
    app.config["MAIL_USE_SSL"] = True
else:
    app.config["MAIL_USE_SSL"] = False
mail_from = os.environ.get("SENDMAIL_FROM", sendmail_from_default)
mail_base_url = os.environ.get("SENDMAIL_BASE_URL", sendmail_from_default)
# Lectura del template para los mails de recovery
mail_template = helpers.loadTextFile("templates/mailTemplate.html")
mail = Mail(app)
# Lectura del secret para los token jwt
jwt_secret = os.environ.get("JWT_SECRET",
                            jwt_secret_default)

# Inicializacion de Google login
google_client_id = os.environ.get("GOOGLE_CLIENT_ID",
                                  google_client_id_default)

# Inicializacion del parser de request ID
RequestID(app)

# Habilitacion de CORS
CORS(app)

# Inicializacion de JWT
app.config["JWT_SECRET_KEY"] = jwt_secret
jwt = JWTManager(app)

# Lectura de la configuración de ambiente
app_env = os.environ.get("APP_ENV", app_env_default)
# Lectura de la API KEY
api_key = os.environ.get("APP_SERVER_API_KEY", api_key_default)
# Lectura de longitud de sesion
session_length_user = os.environ.get("SESSION_LENGTH_USER_MINUTES",
                                     session_length_minutes_default_user)
session_length_admin = os.environ.get("SESSION_LENGTH_ADMIN_MINUTES",
                                      session_length_minutes_default_admin)
# Lectura de longitud de recovery
recovery_length = os.environ.get("RECOVERY_LENGTH_MINUTES",
                                 recovery_length_minutes_default)
# Lectura del intervalo de limpieza de sessions, en segundos
prune_interval_sessions = \
                        os.environ.get("PRUNE_INTERVAL_SESSIONS_SECONDS",
                                       prune_interval_sessions_seconds_default)
# Lectura del intervalo de limpieza de recovery, en segundos
prune_interval_recovery = \
                        os.environ.get("PRUNE_INTERVAL_RECOVERY_SECONDS",
                                       prune_interval_recovery_seconds_default)
# Lectura de la longitud maxima para usernames
username_max_length = os.environ.get("USERNAME_MAX_LENGTH",
                                     username_max_length_default)
# Lectura de la politica de configuracion de contrasenias
password_policy = {
    "min": os.environ.get("PASSWORD_POLICY_MIN",
                          password_policy_default["min"]),
    "max": os.environ.get("PASSWORD_POLICY_MAX",
                          password_policy_default["max"]),
    "digits": os.environ.get("PASSWORD_POLICY_DIGITS",
                             password_policy_default["digits"]),
    "letters": os.environ.get("PASSWORD_POLICY_LETTERS",
                              password_policy_default["letters"]),
    "lowercase": os.environ.get("PASSWORD_POLICY_LOWERCASE",
                                password_policy_default["lowercase"]),
    "uppercase": os.environ.get("PASSWORD_POLICY_UPPERCASE",
                                password_policy_default["uppercase"]),
    "symbols": os.environ.get("PASSWORD_POLICY_SYMBOLS",
                              password_policy_default["symbols"])
}
# Lectura de las dimensiones para las imagenes de avatar
avatar_max_width = os.environ.get("AVATAR_MAX_WIDTH",
                                  avatar_max_width_default)
avatar_max_height = os.environ.get("AVATAR_MAX_HEIGHT",
                                   avatar_max_height_default)
avatar_max_size = os.environ.get("AVATAR_MAX_SIZE",
                                 avatar_max_size_default)
# Lectura de la configuracion del servidor de base de datos
mongodb_hostname = os.environ.get("MONGODB_HOSTNAME",
                                  mongodb_hostname_default)
mongodb_database = os.environ.get("MONGODB_DATABASE",
                                  mongodb_database_default)
mongodb_username = os.environ.get("MONGODB_USERNAME",
                                  mongodb_username_default)
mongodb_password = os.environ.get("MONGODB_PASSWORD",
                                  mongodb_password_default)
mongodb_ssl = os.environ.get("MONGODB_SSL",
                             mongodb_ssl_default)
mongodb_replica_set = os.environ.get("MONGODB_REPLICA_SET",
                                     mongodb_replica_set_default)
mongodb_auth_source = os.environ.get("MONGODB_AUTH_SOURCE",
                                     mongodb_auth_source_default)

# Inicializacion de la base de datos, MongoDB
app.config["MONGO_URI"] = "mongodb://" + \
                          mongodb_username + \
                          ":" + \
                          mongodb_password + \
                          "@" + \
                          mongodb_hostname + \
                          "/" + \
                          mongodb_database + \
                          "?ssl=" + \
                          mongodb_ssl +\
                          ("" if (mongodb_replica_set == "None") else
                              ("&replicaSet=" + mongodb_replica_set)) + \
                          ("" if (mongodb_auth_source) == "None" else
                              ("&authSource=" + mongodb_auth_source)) + \
                          "&retryWrites=true" + \
                          "&w=majority"

mongo = PyMongo(app)
db = mongo.db
cl = mongo.cx


# Inicializacion - para cuando ejecuta gunicorn + flask
# Server hook "on_starting", ejecuta 1 sola vez antes de forkear los workers
def on_starting(server):
    # Ejemplos de logs, para los distintos niveles
    # app.logger.debug('This is a DEBUG message!')
    # app.logger.info('This is an INFO message!')
    # app.logger.warning('This is a WARNING message!')
    # app.logger.error('This is an ERROR message!')
    # app.logger.critical('This is a CRITICAL message!')

    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.logger.debug("Log system configured for Gunicorn.")

    # Logueo de los valores configurados mediante variables de entorno
    helpers.config_log()

    # Inicializacion del scheduler utilizado para limpiar las collections
    # de tokens vencidos
    app.logger.debug("Configuring BackgroundScheduler for Gunicorn.")
    global scheduler
    scheduler = BackgroundScheduler(timezone="UTC", daemon=True)

    # Limpia la tabla de sesiones vencidas
    # Frecuencia PRUNE_INTERVAL_SESSIONS_SECONDS
    app.logger.debug("Configuring session prune job, interval " +
                     str(prune_interval_sessions) + " seconds.")
    scheduler.add_job(func=helpers.prune_sessions,
                      coalesce=True,
                      max_instances=1,
                      trigger="interval",
                      seconds=int(prune_interval_sessions),
                      id="auth_server_prune_sessions",
                      replace_existing=True)

    # Limpia la tabla de recoveries vencidas
    # Frecuencia PRUNE_INTERVAL_RECOVERY_SECONDS
    app.logger.debug("Configuring recovery prune job, interval " +
                     str(prune_interval_recovery) + " seconds.")
    scheduler.add_job(func=helpers.prune_recovery,
                      coalesce=True, max_instances=1,
                      trigger="interval",
                      seconds=int(prune_interval_recovery),
                      id="auth_server_prune_recovery",
                      replace_existing=True)

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


# Request log, inicializacion de los decorators
# Llamada antes de cada request
@app.before_request
def before_request():
    app.logger.debug(helpers.log_request_id() +
                     'Excecuting before request actions.')
    requestlog.start_timer()


# Llamada luego de cada request
@app.after_request
def after_request(response):
    app.logger.debug(helpers.log_request_id() +
                     'Excecuting after request actions.')
    requestlog.log_request(response)

    return response


# Defincion de los endpoints del server
api.add_resource(home.Home,
                 "/")
api.add_resource(home.Ping,
                 "/ping")
api.add_resource(home.Stats,
                 "/stats")
api.add_resource(home.Status,
                 "/status")
api.add_resource(adminusers.AllAdminUsers,
                 api_path + "/adminusers")
api.add_resource(adminusers.AdminUser,
                 api_path + "/adminusers/<string:username>")
api.add_resource(adminusers.AdminUserSessions,
                 api_path + "/adminusers/<string:username>/sessions")
api.add_resource(users.AllUsers,
                 api_path + "/users")
api.add_resource(users.User,
                 api_path + "/users/<string:username>")
api.add_resource(users.UserSessions,
                 api_path + "/users/<string:username>/sessions")
api.add_resource(sessions.AllSessions,
                 api_path + "/sessions")
api.add_resource(sessions.Session,
                 api_path + "/sessions/<string:token>")
api.add_resource(recovery.AllRecovery,
                 api_path + "/recovery")
api.add_resource(recovery.Recovery,
                 api_path + "/recovery/<string:username>")
api.add_resource(requestlog.RequestLog,
                 api_path + "/requestlog")

# Wrappeamos con Talisman a la aplicacion Flask
# Solo permitimos http para el ambiente de desarrollo
Talisman(app,
         force_https=(False if app_env == "DEV" else True),
         content_security_policy=None)

# Inicio del server en forma directa con WSGI
# Toma el puerto y modo de las variables de entorno
# PORT
# APP_DEBUG - "True, False"
if __name__ == '__main__':
    # Si se ejecuta con WSGI, el log level es DEBUG
    app.logger.setLevel("DEBUG")
    app.logger.debug("Log system configured for WSGI.")
    # Seteo de modo debug y puerto - tomado de variables de entorno
    ENVIRONMENT_DEBUG = os.environ.get("APP_DEBUG",
                                       app_debug_default)
    ENVIRONMENT_PORT = os.environ.get("APP_PORT", os.environ.get("PORT",
                                      app_port_default))
    # Logueo de los valores configurados mediante variables de entorno
    helpers.config_log()
    app.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
