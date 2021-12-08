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
#Passlib para encriptar contrasenias
from passlib.apps import custom_app_context
from functools import wraps
#PyMongo para el manejo de MongoDB
from flask_pymongo import PyMongo

#Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers

#Clase que muestra la info del server, en la home '/'
class Home(Resource):
    @helpers.log_reqId
    def get(self):
        homeResponseGet = "7599-cloudsync-auth-server-v" + authServer.server_version
        authServer.app.logger.info(helpers.log_request_id() + 'Displaying home with server information.')
        return helpers.return_request(homeResponseGet, HTTPStatus.OK)

#Clase que devuelve el ping del servidor
class Ping(Resource):
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() + 'Ping requested.')        
        pingResponseGet = {
            "code": 0,
            "message": "Ping.",
            "data": None
        }
        return helpers.return_request(pingResponseGet, HTTPStatus.OK)
