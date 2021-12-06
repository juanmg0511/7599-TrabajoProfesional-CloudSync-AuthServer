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
from functools import wraps
#PyMongo para el manejo de MongoDB
from flask_pymongo import PyMongo

#Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers

#Clase que define el endpoint para trabajar con usuarios
#Operaciones CRUD: Create, Read, Update, Delete
#verbo GET - listar usuarios
class AllUsers(Resource):
    #verbo GET - listar usuarios
    @helpers.require_apikey
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() + 'All users requested.')
        
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("show_closed", type=helpers.non_empty_string, required=False, nullable=False)
            args = parser.parse_args()
        except:
            AllUsersResponseGet = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(AllUsersResponseGet, HTTPStatus.BAD_REQUEST)                
        
        show_closed = str(args.get("show_closed", "False"))
        if (str(show_closed).lower().replace("\"", "").replace("'", "") == "true"):
            show_closed = True
        else:
            show_closed = False
            
        if (show_closed == True):
            allUsers = authServer.db.users.find()
        else:
            allUsers = authServer.db.users.find({"account_closed": False})

        AllUsersResponseGet = []        
        for existingUser in allUsers:
            retrievedUser = {
                "id": str(existingUser["_id"]),
                "username": existingUser["username"],
                "first_name": existingUser["first_name"],
                "last_name":  existingUser["last_name"],
                "contact": existingUser["contact"],
                "avatar": existingUser["avatar"],
                "login_service": existingUser["login_service"],                
                "account_closed": existingUser["account_closed"],
                "date_created": existingUser["date_created"],
                "date_updated": existingUser["date_updated"]                
            }
            AllUsersResponseGet.append(retrievedUser)
        return helpers.return_request(AllUsersResponseGet, HTTPStatus.OK)
