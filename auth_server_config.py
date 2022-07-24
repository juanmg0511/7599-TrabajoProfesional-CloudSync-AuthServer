# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# auth_server_config.py

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# OS para leer variables de entorno y logging para escribir los logs
import os


###############################################################################
#
# Seccion de Configuracion
#
###############################################################################


# Version de API y Server
api_version = "1"
server_version = "1.00"


###############################################################################
#
# Seccion de Valores por default
#
###############################################################################


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


###############################################################################
#
# Seccion de lectura de variables de entorno
# Lee de docker-compose.yml al ejecutar el ambiente DEV
#
###############################################################################


# Configuracion del sistema de correo
sendmail_active = os.environ.get("SENDMAIL_ACTIVE",
                                 sendmail_active_default)
sendmail_server = os.environ.get("SENDMAIL_SERVER",
                                 sendmail_server_default)
sendmail_port = os.environ.get("SENDMAIL_PORT",
                               sendmail_port_default)
sendmail_username = os.environ.get("SENDMAIL_USERNAME",
                                   sendmail_username_default)
sendmail_password = os.environ.get("SENDMAIL_PASSWORD",
                                   sendmail_password_default)
sendmail_tls = os.environ.get("SENDMAIL_USE_TLS",
                              sendmail_tls_default)
sendmail_ssl = os.environ.get("SENDMAIL_USE_SSL",
                              sendmail_ssl_default)
sendmail_from = os.environ.get("SENDMAIL_FROM",
                               sendmail_from_default)
sendmail_base_url = os.environ.get("SENDMAIL_BASE_URL",
                                   sendmail_base_url_default)
if (sendmail_active == "1"):
    sendmail_active = True
else:
    sendmail_active = False

# Lectura del secret para los token jwt
jwt_secret = os.environ.get("JWT_SECRET",
                            jwt_secret_default)


# Inicializacion de Google login
google_client_id = os.environ.get("GOOGLE_CLIENT_ID",
                                  google_client_id_default)


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
