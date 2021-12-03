#CloudSync - Auth Server
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
from functools import wraps
#PyMongo para el manejo de MongoDB
from flask_pymongo import PyMongo

#Importacion del archivo principal
import auth_server as authServer

#Decorator que valida la API key provista en los request headers
def require_apikey(view_function):
    @wraps(view_function)
    def check_apikey_decorated(*args, **kwargs):
        authServer.app.logger.debug(log_request_id() + "Checking API KEY for client ID: \"" + str(request.headers.get("X-Client-ID")) + "\".")
        if request.headers.get("X-Client-ID") and request.headers.get("X-Client-ID") == authServer.api_key:
            authServer.app.logger.debug(log_request_id() + "Authorized.")
            return view_function(*args, **kwargs)
        else:
            ApiResponseUnauthorized = {
                "code": -1,
                "message": "You are not authorized to access this resource.",
                "data": None
            }
            return return_request(ApiResponseUnauthorized,HTTPStatus.UNAUTHORIZED)
    return check_apikey_decorated

#Decorator que loguea el request ID de los headers como info
def log_reqId(view_function):
    @wraps(view_function)
    def check_and_log_req_id(*args, **kwargs):
        authServer.app.logger.info(log_request_id() + "Request ID: \"" + str(current_request_id()) + "\".")            
        return view_function(*args, **kwargs)
    return check_and_log_req_id

#Funcion que devuelve los return de los requests
def return_request(message, status):

    #Loguea el mensaje a responder, y su codigo HTTP
    authServer.app.logger.debug(log_request_id() + str(message))
    authServer.app.logger.info(log_request_id() + "Returned HTTP: " + str(status.value))

    return message, status

#Funcion que devuelve el request id, o None si no aplica, formateado para el log default de Gunicorn
def log_request_id():
    return "[" + str(current_request_id()) + "] "