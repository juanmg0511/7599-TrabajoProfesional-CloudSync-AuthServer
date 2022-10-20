# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# src/helpers.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
import io
import re
from datetime import date, datetime, timedelta
# Flask, para la implementacion del servidor REST
from flask import request
from flask_log_request_id import current_request_id
from http import HTTPStatus
# Flask-sendmail para el envio de correo
from flask_mail import Message
# base64, math y PIL para la validacion de los avatars
import base64
import math
from PIL import Image
# Validators, para la validacion de mails y URLs
import validators
# Python-Usernames, para la validacion de nombres de usuario
from usernames import is_safe_username
# Password-Validator, para la validacion de contrasenias
from password_validator import PasswordValidator
# Wraps, para implementacion de decorators
from functools import wraps

# Importacion de las configuracion del Auth Server
import auth_server_config as config
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
           == config.api_key:
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


# Funcion que devuelve el mensaje de error en caso que se produzca algun
# problema durante la ejecucion de una operacion con la base de datos de
# logs
def handleLogDatabasebError(e):

    authServer.app.logger.warning(log_request_id() + "Error excecuting a " +
                                  "log database operation: " +
                                  str(e))

    return


# Funcion que devuelve el mensaje de error y se encarga de finalizar el
# request en caso que se produzca algun problema durante la ejecucion de
# una operacion con la base de datos
def handleDatabasebError(e):

    authServer.app.logger.error(log_request_id() + "Error excecuting a " +
                                "database operation. Please try again later.")

    DatabaseErrorResponse = {
        "code": -1,
        "message": "Error excecuting a database operation. " +
                   "Please try again later.",
        "data": str(e)
    }

    return return_request(DatabaseErrorResponse,
                          HTTPStatus.SERVICE_UNAVAILABLE)


# Funcion que loguea los parametros configurados en variables de entorno
def config_log():

    if (config.app_env != "PROD"):
        authServer.app.logger.warning("**************************************")
        authServer.app.logger.warning("* This server is: " +
                                      config.app_env)
        authServer.app.logger.warning("**************************************")

    authServer.app.logger.info("Database server: " +
                               config.mongodb_hostname)
    authServer.app.logger.debug("Database name: " +
                                config.mongodb_database)
    authServer.app.logger.debug("Log database name: " +
                                config.mongodb_log_database)
    authServer.app.logger.debug("Database username: " +
                                config.mongodb_username)
    authServer.app.logger.debug("Database using SSL: " +
                                config.mongodb_ssl)
    authServer.app.logger.info("Database replica set: " +
                               config.mongodb_replica_set)
    authServer.app.logger.debug("Database auth source: " +
                                config.mongodb_auth_source)

    if (config.api_key == config.api_key_default):
        authServer.app.logger.warning("API key not set, please verify " +
                                      "\"APP_SERVER_API_KEY\". Using " +
                                      "default value.")
    authServer.app.logger.debug("API key is: \"" +
                                str(config.api_key) +
                                "\".")
    authServer.app.logger.info("Session length for users is: " +
                               str(config.session_length_user) +
                               " minutes.")
    authServer.app.logger.info("Session length for admins is: " +
                               str(config.session_length_admin) +
                               " minutes.")
    authServer.app.logger.info("Recovery length is: " +
                               str(config.recovery_length) +
                               " minutes.")
    authServer.app.logger.info("Prune interval for sessions is: " +
                               str(config.prune_interval_sessions) +
                               " seconds.")
    authServer.app.logger.info("Prune interval for recovery and stats is: " +
                               str(config.prune_interval_recovery) +
                               " seconds.")
    authServer.app.logger.info("Time period to keep stats is: " +
                               str(config.stats_days_to_keep) +
                               " days.")
    if (config.sendmail_active is False):
        authServer.app.logger.warning("Send mail functionality is DISABLED. " +
                                      "Please enable \"SENDMAIL_ACTIVE\".")
    authServer.app.logger.info("Mail server: \"" +
                               str(authServer.app.config["MAIL_SERVER"]) +
                               "\".")
    authServer.app.logger.info("Port: " +
                               str(authServer.app.config["MAIL_PORT"]) +
                               ".")
    authServer.app.logger.info("Use TLS: " +
                               str(authServer.app.config["MAIL_USE_TLS"]) +
                               ".")
    authServer.app.logger.info("Use SSL: " +
                               str(authServer.app.config["MAIL_USE_SSL"]) +
                               ".")
    authServer.app.logger.info("Recovery base URL: \"" +
                               str(config.sendmail_base_url) +
                               "\".")
    if (config.google_client_id is None):
        authServer.app.logger.warning("Google login incorrectly " +
                                      "configured. " +
                                      "Please check settings!")
    else:
        authServer.app.logger.info("Google login configured.")
        authServer.app.logger.info("Client ID: \"" +
                                   config.google_client_id +
                                   "\".")
    authServer.app.logger.debug("Max avatar width is: \"" +
                                str(config.avatar_max_width) +
                                "\" pixels.")
    authServer.app.logger.debug("Max avatar height is: \"" +
                                str(config.avatar_max_height) +
                                "\" pixels.")
    authServer.app.logger.debug("Max avatar size is: \"" +
                                str(config.avatar_max_size) +
                                "\" Bytes.")

    return 0


# Funcion que limpia la collection de sesiones vencidas
def prune_sessions():

    # Comienzo del proceso
    authServer.app.logger.info("prune_sessions: starting...")

    # Limpieza de sessions
    try:
        result = authServer.db.sessions.delete_many({
            "expires": {"$lt": datetime.utcnow().isoformat()}
        })
        sessionsDeleted = result.deleted_count

    except Exception as e:
        return handleDatabasebError(e)

    authServer.app.logger.info("prune_sessions: deleted " +
                               str(sessionsDeleted) +
                               " expired sessions.")

    # Fin del proceso
    authServer.app.logger.info("prune_sessions: done.")

    # Armamos el documento a guardar en la base de datos
    pruneSession = {
        "log_type": "task",
        "request_date": datetime.utcnow().isoformat(),
        "task_type": "prune expired sessions",
        "api_version": "v" + config.api_version,
        "pruned_sessions": sessionsDeleted
    }
    try:
        authServer.db_log.requestlog.insert_one(pruneSession)
    except Exception as e:
        return handleLogDatabasebError(e)
    authServer.app.logger.debug('Prune expired sessions:' +
                                ' task data successfully logged to DB.')

    return 0


# Funcion que limpia la collection de recovery vencidas, y la
# de stats de registros viejos
def prune_recovery_stats():

    # Comienzo del proceso
    authServer.app.logger.info("prune_recovery_stats: starting...")

    # Limpieza de recovery
    try:
        result = authServer.db.recovery.delete_many({
            "expires": {"$lt": datetime.utcnow().isoformat()}
        })
        recoveryDeleted = result.deleted_count

    except Exception as e:
        return handleDatabasebError(e)

    authServer.app.logger.info("prune_recovery: deleted " +
                               str(recoveryDeleted) +
                               " expired requests.")

    # Limpieza de stats
    limitDate = date.today() - timedelta(days=int(config.stats_days_to_keep))
    try:
        result = authServer.db_log.stats.delete_many({
            "date": {"$lt": str(limitDate)}
        })
        statsDeleted = result.deleted_count

    except Exception as e:
        return handleLogDatabasebError(e)

    authServer.app.logger.info("prune_stats: deleted " +
                               str(statsDeleted) +
                               " expired stats records.")

    # Fin del proceso
    authServer.app.logger.info("prune_recovery_stats: done.")

    # Armamos el documento a guardar en la base de datos
    pruneLog = {
        "log_type": "task",
        "request_date": datetime.utcnow().isoformat(),
        "task_type": "prune expired recovery requests and stats records",
        "api_version": "v" + config.api_version,
        "pruned_requests": recoveryDeleted,
        "pruned_stats": statsDeleted
    }
    try:
        authServer.db_log.requestlog.insert_one(pruneLog)
    except Exception as e:
        return handleLogDatabasebError(e)
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
    if ((not s) or (str.isspace(s))):
        raise ValueError("Must not be empty string.")
    return s


# Funcion que chequea si un argumento esta vacio
def non_empty_argument(a):
    if not a:
        raise ValueError("Must not be empty.")
    return a


# Funcion que chequea si una fecha es valida
def non_empty_date(d):
    try:
        d = datetime.strptime(d, "%Y-%m-%d")
    except Exception:
        raise ValueError("Must be valid date.")
    return d


# Funcion que chequea si un bool es valido
def non_empty_bool(b):
    if (str(b).lower() == "true"
       or
       str(b).lower() == "false"):
        return b
    else:
        raise ValueError("Must be valid bool.")


# Funcion que chequea si un email es valido
def non_empty_email(e):
    if (not validators.email(e)):
        raise ValueError("Must be valid email.")
    return e


# Funcion que chequea si una url es valida
def non_empty_url(u):
    if (not validators.url(u)):
        raise ValueError("Must be valid URL.")
    return u


# Funcion que chequea si una imagen de avatar es valida (base64)
# Configuracion mediante variables de entorno
# Ancho maximo (px): AVATAR_MAX_WIDTH
# Altura maxima (px): AVATAR_MAX_HEIGHT
# Tamanio limite (B): AVATAR_MAX_SIZE
def non_empty_image(i):
    # Validamos si el string pasado por parametro es una imagen
    try:
        image = base64.b64decode(i)
        img = Image.open(io.BytesIO(image))
    except Exception:
        raise ValueError("Must be valid base64 encoded image.")

    # Validacion de formatos
    if img.format.lower() in ["jpg", "jpeg", "png"]:
        # Validacion de ancho y alto
        width, height = img.size
        if (width <= int(config.avatar_max_width)
           and height <= int(config.avatar_max_height)):
            # Validacion de tamanio
            fileSize = math.ceil(len(i) / 4) * 3
            if (fileSize <= int(config.avatar_max_size)):
                return ("data:image/" +
                        img.format.lower() +
                        ";base64," +
                        i)
            else:
                raise ValueError("Image size exceeds the " +
                                 "maximum allowed value.")
        else:
            raise ValueError("Image dimensions exceed the " +
                             "maximum allowed values.")
    else:
        raise ValueError("Image must be in jpg or png format.")


# Funcion que chequea si un nombre de usario es valido
#
# https://pypi.org/project/python-usernames/
#
# Provides a default regex validator.
# Validates against list of banned words that should not be used as username.
#
# The default regular expression is as follows:
# ^                  beginning of string
# (?!_$)             no only _
# (?![-.])           no - or . at the beginning
# (?!.*[_.-]{2})     no __ or _. or ._ or .. or -- inside
# [a-zA-Z0-9_.-]+    allowed characters, atleast one must be present
# (?<![.-])          no - or . at the end
# $                  end of string
def non_empty_and_safe_username(u):
    if is_safe_username(u,
                        max_length=int(
                            config.username_max_length)) is False:
        raise ValueError("Invalid username.")
    return u


# Funcion que chequea si un nombre de usario es seguro para usar como filtro
def non_empty_and_safe_filter_username(u):

    if (not re.match("^[a-zA-Z0-9_.]+$", u)):
        raise ValueError("Invalid username.")
    return u


# Funcion que chequea si una contrasenia es valida
#
# https://pypi.org/project/password-validator/
#
# Rules supported as of now are:
# digits()	    specifies password must include digits
# letters()	    specifies password must include letters
# lowercase()	specifies password must include lowercase letters
# uppercase()	specifies password must include uppercase letters
# symbols()	    specifies password must include symbols
# spaces()	    specifies password must include spaces
# min(len)	    specifies minimum length
# max(len)	    specifies maximum length

# Create a schema
# schema = PasswordValidator()
#
# Add properties to it
# schema\
# .min(8)\
# .max(100)\
# .has().uppercase()\
# .has().lowercase()\
# .has().digits()\
# .has().no().spaces()\
#
# Validate against a password string
# print(schema.validate('validPASS123'));
# => True
# print(schema.validate('invalidPASS'));
# => False
def non_empty_and_valid_password(p):

    # Instanciacion y configuracion de la politica de
    # contrasenias. Por default no se permiten passwords con
    # espacios.
    #
    # Hay que armarlo como string y ejecutarlo una sola vez porque
    # no se pueden agregar condiciones dinamicamente al objeto.
    passwordSchema = PasswordValidator()
    passwordSchemaStr = "passwordSchema" + \
                        ".min(int(config.password_policy[\"min\"]))" + \
                        ".max(int(config.password_policy[\"max\"]))"
    if (config.password_policy["digits"] in ["True", "true", True]):
        passwordSchemaStr += ".has().digits()"
    if (config.password_policy["letters"] in ["True", "true", True]):
        passwordSchemaStr += ".has().letters()"
    if (config.password_policy["uppercase"] in ["True", "true", True]):
        passwordSchemaStr += ".has().uppercase()"
    if (config.password_policy["lowercase"] in ["True", "true", True]):
        passwordSchemaStr += ".has().lowercase()"
    if (config.password_policy["symbols"] in ["True", "true", True]):
        passwordSchemaStr += ".has().symbols()"
    passwordSchemaStr += ".has().no().spaces()"

    # Ejecucion de la sentencia, a fin de configurar la politica
    exec(passwordSchemaStr)

    # Chequeo del valor ingresado y devolucion de resultado
    if passwordSchema.validate(p) is False:
        raise ValueError("Invalid password.")
    return p


# Funcion que envia el correo de recupero de contraseña
def send_recovery_notification(user, recovery_key, force_send=False):

    authServer.app.logger.info(log_request_id() +
                               "Sending mail to user: \"" +
                               str(user["username"]) +
                               "\" at \"" +
                               str(user["contact"]["email"]) + "\".")

    if (config.sendmail_active is False and force_send is False):
        authServer.app.logger.warning(log_request_id() +
                                      "Send mail functionality is " +
                                      "DISABLED. Please enable " +
                                      "\"SENDMAIL_ACTIVE\".")
        authServer.app.logger.warning(log_request_id() +
                                      "Mail not sent.")
        return -1

    accent_color = None
    cs_logo = None
    if config.app_env == "QA":
        subject = "FIUBA CloudSync [Quality Assurance]"
        accent_color = config.color_qa
        cs_logo = authServer.logo_cs_qa
    elif config.app_env == "PROD":
        subject = "FIUBA CloudSync"
        accent_color = config.color_prod
        cs_logo = authServer.logo_cs_prod
    else:
        subject = "FIUBA CloudSync [Development]"
        accent_color = config.color_dev
        cs_logo = authServer.logo_cs_dev

    msg = Message(subject + ": password recovery request",
                  sender=("FIUBA CloudSync Admin", config.sendmail_from),
                  reply_to="no-reply@fiuba-cloudsync.com",
                  recipients=[str(user["contact"]["email"])])

    msg.html = authServer.\
        mail_template.\
        replace("#5B9CFF",
                accent_color).\
        replace("wwww://wwwww-wwwwww-w-www-wwwww.wwwwwwwww.www",
                config.sendmail_base_url).\
        replace("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                recovery_key).\
        replace("yyyy-yyyy-yyyy",
                user["username"]).\
        replace("zzzz-zzzz-zzzz",
                cs_logo)
    message = "Mail dispatched successfully."
    exception = None
    try:
        with authServer.app.app_context():
            authServer.mail.send(msg)
        authServer.app.logger.info(log_request_id() + message)
    except Exception as e:
        message = "Error sending mail."
        exception = str(e)
        authServer.app.logger.error(log_request_id() + message)
        authServer.app.logger.error(log_request_id() + "Message: " + exception)
    finally:
        # Armamos el documento a guardar en la base de datos
        mailLog = {
            "log_type": "mail",
            "request_date": datetime.utcnow().isoformat(),
            "request_id": current_request_id(),
            "api_version": "v" + config.api_version,
            "username": user["username"],
            "email": str(user["contact"]["email"]),
            "recovery_key": recovery_key,
            "mail_status": message,
            "exception_message": exception
        }
        try:
            authServer.db_log.requestlog.insert_one(mailLog)
        except Exception as e:
            return handleLogDatabasebError(e)
        authServer.app.logger.debug(log_request_id() +
                                    'Mail data successfully logged to DB.')

    return 0


# Devuelve el contenido del archivo pasado por parametro
def loadTextFile(path):
    try:
        with open(path, "r") as path_fp:
            return str(path_fp.read())
    except Exception as e:
        return e
