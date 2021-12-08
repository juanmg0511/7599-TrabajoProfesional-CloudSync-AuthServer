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

#Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers

#Clase que define el endpoint para trabajar con usuarios
#Operaciones CRUD: Create, Read, Update, Delete
#verbo GET - listar usuarios
#verbo POST - nuevo usario
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

    #verbo POST - nuevo usario
    @helpers.require_apikey
    @helpers.log_reqId
    def post(self):     
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("username", type=helpers.non_empty_string, required=True, nullable=False)
            parser.add_argument("password", type=helpers.non_empty_string, required=False , nullable=False)
            parser.add_argument("first_name", type=helpers.non_empty_string, required=True, nullable=False)
            parser.add_argument("last_name", type=helpers.non_empty_string, required=True, nullable=False)
            parser.add_argument("contact", type=dict, required=True, nullable=False)
            parser.add_argument("avatar", type=dict, required=False, nullable=True)
            parser.add_argument("login_service", type=helpers.non_empty_bool, required=False, nullable=False)
            args = parser.parse_args()
        except:
            UserResponsePost = {
                "code": -1,
                "message": "Bad request. Missing required arguments.",
                "data": None
            }
            return helpers.return_request(UserResponsePost, HTTPStatus.BAD_REQUEST)        
        
        #Validacion requeridos en contact
        try:
            email = helpers.non_empty_email(args["contact"].get("email", ""))
            phone = helpers.non_empty_string(args["contact"].get("phone", ""))  
        except:
            UserResponsePost = {
                "code": -2,
                "message": "Bad request. Wrong format for 'contact'.",
                "data": None
            }            
            return helpers.return_request(UserResponsePost, HTTPStatus.BAD_REQUEST) 

        #Validacion de avatar
        if (isinstance(args["avatar"], dict)):
            try:
                url = helpers.non_empty_avatar(args["avatar"].get("url", ""))  
            except:
                UserResponsePost = {
                    "code": -3,
                    "message": "Bad request. Wrong format for 'avatar'.",
                    "data": None
                }
                return helpers.return_request(UserResponsePost, HTTPStatus.BAD_REQUEST)
        else:
            url = None

        #Validacion del tipo de usuario
        #Por default es false, para que el cambio sea transparente
        login_service = False
        if ((args["login_service"] == True) or (args["login_service"] == False) ):
            login_service = args["login_service"]
        
        try:
            if (login_service == True):
                #Si es true, no debe proporcionar una password
                if (args["password"] is not None):
                    raise ValueError("Must not supply password with login service.")
                
            else:
                #Si es false, debe proporcionar una password, y no debe estar vacia
                if (args["password"] is not None):
                    password = args["password"]
                else:
                    raise ValueError("Password is required without login service.")
                
        except ValueError as v:
            UserResponsePost = {
                "code": -4,
                "message": "Bad request. Wrong combination of 'login_service' and 'password', please see API documentation.",
                "data": str(v)
            }
            return helpers.return_request(UserResponsePost, HTTPStatus.BAD_REQUEST)            
        
        authServer.app.logger.info(helpers.log_request_id() + "New user '" + args["username"] + "' requested.")
                 
        existingUser = authServer.db.users.find_one({"username": args["username"]})
        existingAdminUser = authServer.db.adminusers.find_one({"username": args["username"]})
        if ((existingUser is not None) or (existingAdminUser is not None)):
            UserResponsePost = {
                "code": -5,
                "message": "Bad request. User '" + args["username"] + "' already exists.",
                "data": None
            }
            return helpers.return_request(UserResponsePost, HTTPStatus.BAD_REQUEST)            
        
        userToInsert = {
            "username": args["username"],
            "first_name": args["first_name"],
            "last_name": args["last_name"],
            "contact": {
                            "email": email,
                            "phone": phone
                        },
            "avatar": { "url": url },
            "account_closed": False,
            "login_service": login_service,
            "date_created": datetime.utcnow().isoformat(),
            "date_updated": None
        }
        if (login_service == False):
            userToInsert["password"] = custom_app_context.hash(password)
        UserResponsePost = userToInsert.copy()
        authServer.db.users.insert_one(userToInsert)
        id_userToInsert = str(userToInsert["_id"])
        UserResponsePost["id"] = id_userToInsert
        UserResponsePost.pop("password", None)
        
        return helpers.return_request(UserResponsePost, HTTPStatus.CREATED)
