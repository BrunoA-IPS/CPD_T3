"""
 Flask REST application

"""

import os
from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse, abort
# https://flask-restful.readthedocs.io/en/latest/quickstart.html

from models import Database



IS_DEVELOPMENT = True



# ==========
#  Database
# ==========

# Creates an sqlite database in memory
db = Database(filename=':memory:', schema=f'{os.getcwd()}{"/schema.sql" if IS_DEVELOPMENT else "/CPD_T3/schema.sql"}')
db.recreate()



# ==========
#  Settings
# ==========

app = Flask(__name__)
app.config['STATIC_URL_PATH'] = '/static'
app.config['DEBUG'] = True

api = Api(app)



# ===========
#  Web views
# ===========

class WebViewIndex(Resource):
    """ Returns the web page """
    def get(self):
        """ Returns the web page """
        return app.send_static_file('index.html')
api.add_resource(WebViewIndex, "/")



# ===========
#  API Utils
# ===========

HTTP_CODES = {
    "BadRequest": 400,
    "Unauthorized": 401,
    "Forbidden": 403,
    "NotFound": 404,
}

class ApiBodyParser(reqparse.RequestParser):
    """ Class to parse the Request Body arguments """
    def __init__(self, *arguments: str | tuple[str, bool]):
        super().__init__()

        # iterate over the arguments and add it
        for argument in arguments:
            if isinstance(argument, tuple):
                self.add_argument(argument[0], required=argument[1])
            else:
                self.add_argument(argument)

    def parse(self) -> dict[str, str | int]:
        """ Parse the request body and return a dict with all the properties """
        return super().parse_args()



class ApiUserAuth():
    """ User authorization validator """

    def __init__(self):
        if not request.authorization:
            abort(HTTP_CODES["Forbidden"], message="No present authorization")

        # Store authorization
        setattr(self, "__username__", request.authorization.get("username"))
        setattr(self, "__password__", request.authorization.get("password"))

    def __getitem__(self, item):
        return getattr(self, item)

    @property
    def username(self) -> str:
        """ Get sent username """
        return self["__username__"]
    @property
    def password(self) -> str:
        """ Get sent password """
        return self["__password__"]
    @property
    def id(self) -> str:
        """ Get found id """
        return self["__id__"]

    def validate(self):
        """ Validates if the user is authorized """

        # Verifies if there is no data
        if not self["username"] or not self["password"]:
            abort(HTTP_CODES["Forbidden"], message="No present authorization")

        # Get the user data from the BD
        user_data = db.execute_query("SELECT id FROM user WHERE username=? AND password=?", (
            self["username"], self["password"]
        )).fetchone()

        # Verifies if the credentials are right and the user exists
        if not user_data:
            abort(HTTP_CODES["Forbidden"], message="Invalid authorization")

        # Set the id inside this object
        setattr(self, "__id__", str(user_data["id"]))
        return self



# ===========
#  API views
# ===========

class ApiUserRegister(Resource):
    """ Register endpoint """

    def post(self):
        """ Post to register a new user """

        # Build the parser for this endpoint, and parse the request body
        request_body = ApiBodyParser(("name", True), ("email", True), ("username", True), ("password", True)).parse()

        # Execute SQL query to insert a new user
        new_user_id = str(db.execute_update("INSERT INTO user VALUES (null, ?, ?, ?, ?)", (
            request_body["name"], request_body['email'], request_body["username"], request_body["password"]
        )))

        # get the just inserted user
        user_data = db.execute_query("SELECT * FROM user WHERE id=?", (
            new_user_id
        )).fetchone()

        return make_response(jsonify(user_data))
api.add_resource(ApiUserRegister, "/api/user/register")



class ApiUserLogin(Resource):
    """ Login endpoint """

    def post(self):
        """ Post saying if is a valid login """

        # Parse the body and validates if all arguments are setted
        request_body = ApiBodyParser(("username", True), ("password", True)).parse()

        # Get the user data from the BD
        user_data = db.execute_query("SELECT * FROM user WHERE username=? AND password=?", (
            request_body["username"], request_body["password"]
        )).fetchone()

        # If there is no user, it means its was not a valid authentication
        if not user_data:
            abort(HTTP_CODES["Forbidden"], message="Invalid username and password combination")

        return make_response(jsonify({ "auth": True }))
api.add_resource(ApiUserLogin, "/api/user/login")



class ApiUser(Resource):
    """ User endpoints """

    def get(self):
        """ Return current user """

        # Validates user auth before executing the endpoint
        user_auth = ApiUserAuth().validate()

        # Get the user data from the BD
        user_data = db.execute_query("SELECT * FROM user WHERE id=?", (
            user_auth["id"]
        )).fetchone()

        return make_response(jsonify(user_data))

    def put(self):
        """ Update current user """

        # Get the current user data, using the get endpoint
        user_data: dict[str, str] = ApiUser().get().get_json()

        # Parse the body and validates
        request_body = ApiBodyParser("username", "email", "password", "name").parse()

        # Iterate over request body and replace the data with the wanted to edit to
        for argument in request_body:
            if not request_body[argument]:
                continue
            user_data[argument] = request_body[argument]

        # Execute SQL query to update this user
        db.execute_update("UPDATE user SET name = ?, email = ?, username = ?, password = ? WHERE id = ?;", (
            user_data["name"], user_data['email'], user_data["username"], user_data["password"], user_data["id"]
        ))

        # Return the overwritten data
        return make_response(jsonify(user_data))
api.add_resource(ApiUser, "/api/user")



class ApiProject(Resource):
    """ Projects endpoints """

    def get(self):
        """ Get all projects """

        # Validates user auth before executing the endpoint
        user_auth = ApiUserAuth().validate()

        # Get all the projects from the DB
        user_projects = db.execute_query("SELECT * FROM project WHERE user_id=?", (
            user_auth["id"]
        )).fetchall()

        return make_response(jsonify(user_projects))

    def post(self):
        """ Create a new project """

        # Validates user auth before executing the endpoint, also store the basic user data, username, password and id
        user_auth = ApiUserAuth().validate()

        # Parse the body and validates
        request_body = ApiBodyParser(("title", True), "creation_date", "last_updated").parse()

        # Execute SQL query to insert a new project
        new_project_id = str(db.execute_update("INSERT INTO project VALUES (null, ?, ?, ?, ?)", (
            user_auth["id"], request_body['title'], request_body["creation_date"], request_body["last_updated"]
        )))

        # get the just inserted project
        user_project = db.execute_query("SELECT * FROM project WHERE id=?", (new_project_id)).fetchone()

        return make_response(jsonify(user_project))
api.add_resource(ApiProject, "/api/projects")



class ApiProjectDetails(Resource):
    """ Single project endpoints """

    def get(self, project):
        """ Get details from project """

        # Validates user auth before executing the endpoint
        user_auth = ApiUserAuth().validate()

        # Get the project
        user_project = db.execute_query("SELECT * FROM project WHERE id=? AND user_id=?", (
            project, user_auth["id"]
        )).fetchone()

        # Verify if exists
        if not user_project:
            abort(HTTP_CODES["NotFound"], message="Non existent project")

        return make_response(jsonify(user_project))

    def put(self, project):
        """ Update details of project """

        # Call the endpoint to get the project
        user_project: dict[str, str] = ApiProjectDetails().get(project).get_json()

        # Parse the body and validates
        request_body = ApiBodyParser("title", "creation_date", "last_updated").parse()

        # Iterate over request body and replace the data with the wanted to edit to
        for argument in request_body:
            if not request_body[argument]:
                continue
            user_project[argument] = request_body[argument]

        # Execute SQL query to update the project on the DB
        db.execute_update("UPDATE project SET title = ?, creation_date = ?, last_updated = ? WHERE id = ?;", (
            user_project["title"], user_project['creation_date'], user_project["last_updated"], user_project["id"]
        ))

        # Return the overwritten data
        return make_response(jsonify(user_project))

    def delete(self, project):
        """ Delete project """

        # Call the endpoint to get the project
        ApiProjectDetails().get(project).get_json()

        # Execute SQL query to delete project from DB
        db.execute_update("DELETE FROM project WHERE id = ?;", (
            project
        ))

        return make_response(jsonify({ "deleted": True }))
api.add_resource(ApiProjectDetails, "/api/projects/<string:project>")



class ApiTask(Resource):
    """ Tasks endpoints """

    def get(self, project):
        """ Get tasks list """

        # Validates user auth before executing the endpoint
        user_auth = ApiUserAuth().validate()

        # Call the endpoint to get the project
        ApiProjectDetails().get(project).get_json()

        # Get all the tasks from the DB
        user_tasks = db.execute_query("SELECT task.* FROM project INNER JOIN task ON project.id = task.project_id WHERE project.id = ? AND project.user_id = ?", (
            project, user_auth["id"]
        )).fetchall()

        return make_response(jsonify(user_tasks))

    def post(self, project):
        """ Post new task """

        # Call the endpoint to get the project
        ApiProjectDetails().get(project).get_json()

        # Parse the body and validates
        request_body = ApiBodyParser(("title", True), "creation_date", "completed").parse()

        # Execute SQL query to insert a new task on the DB
        new_task_id = str(db.execute_update("INSERT INTO task VALUES (null, ?, ?, ?, ?)", (
            project, request_body['title'], request_body["creation_date"], request_body["completed"]
        )))

        # get the just inserted task
        user_task = db.execute_query("SELECT * FROM task WHERE id=?", (
            new_task_id
        )).fetchone()

        return make_response(jsonify(user_task))
api.add_resource(ApiTask, "/api/projects/<string:project>/tasks")



class ApiTaskDetails(Resource):
    """ Single task endpoints """

    def get(self, project, task):
        """ Get details from task """

        # Call the endpoint to get the project
        ApiProjectDetails().get(project).get_json()

        # Get the task from the DB
        user_task = db.execute_query("SELECT * FROM task WHERE id=? AND project_id=?", (
            task, project
        )).fetchone()

        # Verify if it exists
        if not user_task:
            abort(HTTP_CODES["NotFound"], message="Non existent task")

        return make_response(jsonify(user_task))

    def put(self, project, task):
        """ Update details from task """

        # Call the endpoint to get the task
        user_task: dict[str, str] = ApiTaskDetails().get(project, task).get_json()

        # Parse the body
        request_body = ApiBodyParser("title", "creation_date", "completed").parse()

        # Iterate over request body and replace the data with the wanted to edit to
        for argument in request_body:
            if not request_body[argument]:
                continue
            user_task[argument] = request_body[argument]

        # Execute SQL query to update the task on the DB
        db.execute_update("UPDATE task SET title = ?, creation_date = ?, completed = ? WHERE id = ?;", (
            user_task["title"], user_task['creation_date'], user_task["completed"], user_task["id"]
        ))

        # Return the overwritten data
        return make_response(jsonify(user_task))

    def delete(self, project, task):
        """ Delete task """

        # Call the endpoint to get the task
        ApiTaskDetails().get(project, task).get_json()

        # Execute SQL query to delete task from DB
        db.execute_update("DELETE FROM task WHERE id = ?;", (
            task
        ))

        return make_response(jsonify({ "deleted": True }))
api.add_resource(ApiTaskDetails, "/api/projects/<string:project>/tasks/<string:task>")



if __name__ == "__main__":
    if IS_DEVELOPMENT:
        app.run(host='0.0.0.0', port=8000)
