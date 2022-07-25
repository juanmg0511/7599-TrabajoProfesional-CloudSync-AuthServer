# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# auth_server.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# Logging para escribir los logs
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

# Importacion de las configuracion del Auth Server
import auth_server_config as config
# Importacion de clases necesarias
from src import home, adminusers, users, sessions, recovery, \
                requestlog, helpers

# Inicializacion de la api
app = Flask(__name__)
api = Api(app)

# Inicializacion del parser de request ID
RequestID(app)

# Habilitacion de CORS
CORS(app)

# Inicializacion de JWT
app.config["JWT_SECRET_KEY"] = config.jwt_secret
jwt = JWTManager(app)

# Configuracion del sistema de correo
app.config["MAIL_SERVER"] = config.sendmail_server
app.config["MAIL_PORT"] = config.sendmail_port
app.config["MAIL_USERNAME"] = config.sendmail_username
app.config["MAIL_PASSWORD"] = config.sendmail_password
if (config.sendmail_tls) == "1":
    app.config["MAIL_USE_TLS"] = True
else:
    app.config["MAIL_USE_TLS"] = False
if (config.sendmail_ssl == "1"):
    app.config["MAIL_USE_SSL"] = True
else:
    app.config["MAIL_USE_SSL"] = False
# Lectura del template para los mails de recovery
mail_template = helpers.loadTextFile("templates/mailTemplate.html")
# Inicializacion del sistema de correo
mail = Mail(app)

# Inicializacion de la base de datos, MongoDB
app.config["MONGO_URI"] = "mongodb://" + \
                          config.mongodb_username + \
                          ":" + \
                          config.mongodb_password + \
                          "@" + \
                          config.mongodb_hostname + \
                          "/" + \
                          config.mongodb_database + \
                          "?ssl=" + \
                          config.mongodb_ssl +\
                          ("" if (config.mongodb_replica_set == "None") else
                              ("&replicaSet=" +
                                  config.mongodb_replica_set)) + \
                          ("" if (config.mongodb_auth_source) == "None" else
                              ("&authSource=" +
                                  config.mongodb_auth_source)) + \
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
                     str(config.prune_interval_sessions) + " seconds.")
    scheduler.add_job(func=helpers.prune_sessions,
                      coalesce=True,
                      max_instances=1,
                      trigger="interval",
                      seconds=int(config.prune_interval_sessions),
                      id="auth_server_prune_sessions",
                      replace_existing=True)

    # Limpia la tabla de recoveries vencidas
    # Frecuencia PRUNE_INTERVAL_RECOVERY_SECONDS
    app.logger.debug("Configuring recovery prune job, interval " +
                     str(config.prune_interval_recovery) + " seconds.")
    scheduler.add_job(func=helpers.prune_recovery,
                      coalesce=True, max_instances=1,
                      trigger="interval",
                      seconds=int(config.prune_interval_recovery),
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
                 config.api_path + "/adminusers")
api.add_resource(adminusers.AdminUser,
                 config.api_path + "/adminusers/<string:username>")
api.add_resource(adminusers.AdminUserSessions,
                 config.api_path + "/adminusers/<string:username>/sessions")
api.add_resource(users.AllUsers,
                 config.api_path + "/users")
api.add_resource(users.User,
                 config.api_path + "/users/<string:username>")
api.add_resource(users.UserSessions,
                 config.api_path + "/users/<string:username>/sessions")
api.add_resource(sessions.AllSessions,
                 config.api_path + "/sessions")
api.add_resource(sessions.Session,
                 config.api_path + "/sessions/<string:token>")
api.add_resource(recovery.AllRecovery,
                 config.api_path + "/recovery")
api.add_resource(recovery.Recovery,
                 config.api_path + "/recovery/<string:username>")
api.add_resource(requestlog.RequestLog,
                 config.api_path + "/requestlog")

# Wrappeamos con Talisman a la aplicacion Flask
# Solo permitimos http para el ambiente de desarrollo
Talisman(app,
         force_https=(False if config.app_env == "DEV" else True),
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
    ENVIRONMENT_DEBUG = config.app_debug
    ENVIRONMENT_PORT = config.app_port
    # Logueo de los valores configurados mediante variables de entorno
    helpers.config_log()
    app.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
