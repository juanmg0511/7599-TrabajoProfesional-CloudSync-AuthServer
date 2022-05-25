# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn

# Basado en:
# https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
# https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876

# Importacion de librerias necesarias
# Flask, para la implementacion del servidor REST
from flask_restful import Resource, reqparse
from http import HTTPStatus

# Importacion del archivo principal y helpers
import auth_server as authServer
from src import helpers


# Clase que muestra la info del server, en la home '/'
class Home(Resource):
    @helpers.log_reqId
    def get(self):
        homeResponseGet = "7599-cloudsync-auth-server-v" + \
                          authServer.server_version
        authServer.app.logger.info(helpers.log_request_id() +
                                   'Displaying home with server information.')
        return helpers.return_request(homeResponseGet, HTTPStatus.OK)


# Clase que devuelve el ping del servidor
class Ping(Resource):
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'Ping requested.')
        pingResponseGet = {
            "code": 0,
            "message": "Ping.",
            "data": None
        }
        return helpers.return_request(pingResponseGet, HTTPStatus.OK)


# Clase que entrega estadisticas del uso del servidor
class Stats(Resource):
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'Server stats requested.')
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("startdate", type=helpers.non_empty_date,
                                required=True, nullable=False)
            parser.add_argument("enddate", type=helpers.non_empty_date,
                                required=True, nullable=False)
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

        if (args["startdate"] > args["enddate"]):
            statsResponseGet = {
                "code": -2,
                "message": "Bad request. Start date greater than end date.",
                "data": None
            }
            return helpers.return_request(statsResponseGet,
                                          HTTPStatus.BAD_REQUEST)

        sort_ascending = str(args.get("sortascending", "False"))
        if (str(sort_ascending).
           lower().
           replace("\"", "").
           replace("'", "") == "true"):
            sort_ascending = True
        else:
            sort_ascending = False

        authServer.app.logger.debug(helpers.log_request_id() +
                                    "Start date: " +
                                    str(args["startdate"].date()))
        authServer.app.logger.debug(helpers.log_request_id() +
                                    "End date: " +
                                    str(args["enddate"].date()))
        authServer.app.logger.debug(helpers.log_request_id() +
                                    "Sort ascending: " +
                                    str(sort_ascending))

        statsResponseGet = helpers.gatherStats(args["startdate"],
                                               args["enddate"], sort_ascending)
        return helpers.return_request(statsResponseGet, HTTPStatus.OK)


# Clase que entrega informacion sobre el estado del servidor
class Status(Resource):
    @helpers.log_reqId
    def get(self):
        authServer.app.logger.info(helpers.log_request_id() +
                                   'Server status requested.')
        dbStatus = "offline"
        try:
            # Informacion sobre la instancia de DB, para DEBUG
            # dbInfo = authServer.cl.server_info()
            dbStatus = "online"
        except Exception:
            dbStatus = "offline"
        statusResponseGet = {
            "code": 0,
            "message": "7599-cloudsync-auth-server-v" +
                       authServer.server_version,
            "data": {
                        "server_status": "online",
                        "database_status": dbStatus
                     }
        }
        return helpers.return_request(statusResponseGet, HTTPStatus.OK)
