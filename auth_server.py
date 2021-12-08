#Cloudsync - Auth Server
#Flask + MongoDB - on Gunicorn

#Basado en:
#https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
#https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

#Importacion de librerias necesarias
#OS para leer variables de entorno y logging para escribir los logs
import sys, os, logging, json, uuid, re, atexit
import time
from datetime import datetime, timedelta   
#Flask, para la implementacion del servidor REST
from flask import Flask, g, request, jsonify
from flask_restful import Api, Resource, reqparse
from flask_log_request_id import RequestID, RequestIDLogFilter, current_request_id
from flask_cors import CORS
from http import HTTPStatus
#Passlib para encriptar contrasenias
from passlib.apps import custom_app_context
from functools import wraps
#PyMongo para el manejo de MongoDB
from flask_pymongo import PyMongo

#Importacion de clases necesarias
from src import home, users, helpers

#Version de API y Server
api_version = "1"
server_version = "1.00"

#Valores default
#Solo para ejecutar en forma directa!
app_debug_default = True
app_port_default = 8000
#Para todos los modos
api_key_default = "44dd22ca-836d-40b6-aa49-7981ded03667"

#Agregamos un root para todos los enpoints, con la api version
api_path = "/api/v" + api_version

#Inicializacion de la api
app = Flask(__name__)
api = Api(app)

#Inicializacion del parser de request ID
RequestID(app)
#Inicializacion de la base de datos, MongoDB
app.config["MONGO_URI"] = "mongodb://" + os.environ.get("MONGODB_USERNAME","authserveruser") + ":" + os.environ.get("MONGODB_PASSWORD","*") + "@" + os.environ.get("MONGODB_HOSTNAME","127.0.0.1") + ":" + os.environ.get("MONGODB_PORT","27017") + "/" + os.environ.get("MONGODB_DATABASE","auth-server-db") + "?retryWrites=false"
mongo = PyMongo(app)
db = mongo.db
cl = mongo.cx

#Habilitacion de CORS
CORS(app)

#Lectura de la API KEY
api_key = os.environ.get("APP_SERVER_API_KEY", api_key_default)

#Inicializacion - para cuando ejecuta gunicorn + flask
#Server hook "on_starting", ejecuta 1 sola vez antes de forkear los workers
def on_starting(server):
    #Ejemplos de logs, para los distintos niveles
    #app.logger.debug('This is a DEBUG message!')
    #app.logger.info('This is an INFO message!')
    #app.logger.warning('This is a WARNING message!')
    #app.logger.error('This is an ERROR message!')
    #app.logger.critical('This is a CRITICAL message!')
    
    gunicorn_logger = logging.getLogger("gunicorn.error")    
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.logger.debug("Log system configured for Gunicorn.")

#Defincion de los endpoints del server
api.add_resource(home.Home, "/")
api.add_resource(home.Ping, "/ping")
api.add_resource(users.AllUsers, api_path + "/users")

# Inicio del server en forma directa con WSGI - toma el puerto y modo de las variables de entorno
# PORT
# APP_DEBUG - "True, False" 
if __name__ == '__main__':
    #Si se ejecuta con WSGI, el log level es DEBUG
    app.logger.setLevel("DEBUG")
    app.logger.debug("Log system configured for WSGI.")
    #Seteo de modo debug y puerto - tomado de variables de entorno
    ENVIRONMENT_DEBUG = os.environ.get("APP_DEBUG", app_debug_default)
    ENVIRONMENT_PORT = os.environ.get("APP_PORT", os.environ.get("PORT", app_port_default))
    #Logueo de los valores configurados mediante variables de entorno
    app.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
