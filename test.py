"""
 Tests the application API

"""

import base64
import unittest
from json import dumps

from app import app, db


def auth_header(username, password):
    """Returns the authorization header."""
    credentials = f'{username}:{password}'
    b64credentials = base64.b64encode(credentials.encode()).decode('utf-8')
    return {'Authorization': f'Basic {b64credentials}'}


class TestBase(unittest.TestCase):
    """Base for all tests."""

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.db = db
        self.db.recreate()

    def tearDown(self):
        pass



class TestRegister(TestBase):
    """ Tests for register endpoint """

    def setUp(self):
        super().setUp()

    def test_register(self):
        """ Tests the registration of a new user """

        body = { "username": "unittest", "password": "unittest", "email": "unittest", "name": "unittest" }

        res = self.client.post('/api/user/register', data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_missing_arguments_register(self):
        """ Tests registration of a new user when missing a argument """

        body = { "username": "unittest", "password": "unittest", "email": "unittest" }

        res = self.client.post('/api/user/register', data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_register_returns(self):
        """ Tests the registration returns the right information on success """

        body = { "username": "unittest", "password": "unittest", "email": "unittest", "name": "unittest" }

        res = self.client.post('/api/user/register', data=dumps(body), content_type='application/json')
        self.assertEqual(res.get_json()["username"], "unittest")



class TestLogin(TestBase):
    """ Tests for login endpoint """

    def setUp(self):
        super().setUp()

    def test_login_successfull(self):
        """ Tests the user login is successfull """

        body = { "username": "homer", "password": "1234" }

        res = self.client.post('/api/user/login', data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_login_not_successfull(self):
        """ Tests the user login is successfull """

        body = { "username": "noaccount", "password": "nopassword" }

        res = self.client.post('/api/user/login', data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 403)



class TestUsers(TestBase):
    """Tests for the user endpoints."""

    def setUp(self):
        super().setUp()

    def test_correct_get(self):
        """ Tests the user information endpoint is sucessfull """

        credentials = auth_header('homer', '1234')

        res = self.client.get('/api/user', headers=credentials)
        self.assertEqual(res.status_code, 200)

    def test_wrong_get(self):
        """ Tests the user information endpoint is not sucessfull """

        credentials = auth_header('no-user', 'no-password')

        res = self.client.get('/api/user', headers=credentials)
        self.assertEqual(res.status_code, 403)

    def test_edit_user(self):
        """ Tests the edit endpoint if returns the sent data """

        credentials = auth_header('homer', '1234')

        body = { "username": "homer_test" }

        res = self.client.put('/api/user', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.get_json()["username"], "homer_test")


class TestProjects(TestBase):
    """Tests for the project endpoints."""

    def setUp(self):
        super().setUp()

    def test_access_endpoint_no_auth(self):
        """ Tests trying to access a tasks endpoint without being authorized """

        res = self.client.get('/api/projects')
        self.assertEqual(res.status_code, 403)

    def test_get_projects(self):
        """ Tests the get of user projects """

        credentials = auth_header('homer', '1234')

        res = self.client.get('/api/projects', headers=credentials)
        self.assertEqual(len(res.get_json()), 2) 

    def test_new_project(self):
        """ Tests the creation of a new user project """

        credentials = auth_header('homer', '1234')

        body = { "title": "test_project" }

        res = self.client.post('/api/projects', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_missing_required_property_to_create_new(self):
        """ Tests the missing required properties when creating a new project """

        credentials = auth_header('homer', '1234')

        body = { "creation_date": "01/01/1990" }

        res = self.client.post('/api/projects', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_get_project(self):
        """ Tests getting a existent project """

        credentials = auth_header('homer', '1234')

        res = self.client.get('/api/projects/1', headers=credentials)
        self.assertEqual(res.status_code, 200)

    def test_get_nonexistent_project(self):
        """ Tests getting a non existent / not from user project """

        credentials = auth_header('homer', '1234')

        res = self.client.get('/api/projects/3', headers=credentials)
        self.assertEqual(res.status_code, 404)

    def test_edit_project(self):
        """ Tests when editing a project returns the sent value """

        credentials = auth_header('homer', '1234')

        body = { "title": "test_new_title" }

        res = self.client.put('/api/projects/1', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.get_json()["title"], body["title"])

    def test_edit_nonexistent_project(self):
        """ Tests trying to edit a project non existent / not from user """

        credentials = auth_header('homer', '1234')

        body = { "title": "test_new_title" }

        res = self.client.put('/api/projects/3', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_delete_project(self):
        """ Tests deleting a project """

        credentials = auth_header('homer', '1234')

        res = self.client.delete('/api/projects/1', headers=credentials)
        self.assertEqual(res.get_json()["deleted"], True)

    def test_delete_nonexistent_project(self):
        """ Tests deleting a project non existent / not from user """

        credentials = auth_header('homer', '1234')

        res = self.client.delete('/api/projects/3', headers=credentials)
        self.assertEqual(res.status_code, 404)



class TestTasks(TestBase):
    """Tests for the tasks endpoints."""

    def setUp(self):
        super().setUp()

    def test_access_endpoint_no_auth(self):
        """ Tests trying to access a tasks endpoint without being authorized """

        res = self.client.get('/api/projects/1/tasks')
        self.assertEqual(res.status_code, 403)

    def test_get_tasks(self):
        """ Tests getting tasks """

        credentials = auth_header('homer', '1234')

        res = self.client.get('/api/projects/1/tasks', headers=credentials)
        self.assertEqual(len(res.get_json()), 2)        

    def test_get_tasks_from_deleted_project(self):
        """ Tests getting a task from a project that got deleted """

        credentials = auth_header('homer', '1234')

        self.client.delete('/api/projects/2', headers=credentials)

        res = self.client.get('/api/projects/2/tasks', headers=credentials)
        self.assertEqual(res.status_code, 404)

    def test_create_new(self):
        """ Tests the creation of a new task """

        credentials = auth_header('homer', '1234')

        body = { "title": "test_project" }

        res = self.client.post('/api/projects/1/tasks', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_missing_required_property_to_create_new(self):
        """ Tests the missing required properties when creating a new task """

        credentials = auth_header('homer', '1234')

        body = { "creation_date": "01/01/1990" }

        res = self.client.post('/api/projects/1/tasks', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_bad_create_nonexistent_project(self):
        """ Tests creating a task on a project that doesnt exists """

        credentials = auth_header('homer', '1234')

        body = { "title": "test_project" }

        res = self.client.post('/api/projects/3/tasks', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_get(self):
        """ Tests getting a task """

        credentials = auth_header('homer', '1234')

        res = self.client.get('/api/projects/1/tasks/1', headers=credentials)
        self.assertEqual(res.status_code, 200)

    def test_get_nonexistent(self):
        """ Tests getting a task that doesnt exists """

        credentials = auth_header('homer', '1234')

        res = self.client.get('/api/projects/1/tasks/6', headers=credentials)
        self.assertEqual(res.status_code, 404)

    def test_get_from_nonexistent_project(self):
        """ Tests getting a task that doesnt exists """

        credentials = auth_header('homer', '1234')

        res = self.client.get('/api/projects/6/tasks/1', headers=credentials)
        self.assertEqual(res.status_code, 404)

    def test_edit(self):
        """ Tests editting a task and it returns the value sent """

        credentials = auth_header('homer', '1234')

        body = { "title": "test_new_title" }

        res = self.client.put('/api/projects/1/tasks/1', headers=credentials, data=dumps(body), content_type='application/json')
        self.assertEqual(res.get_json()["title"], body["title"])

    def test_delete(self):
        """ Tests deleting a task """

        credentials = auth_header('homer', '1234')

        res = self.client.delete('/api/projects/1/tasks/1', headers=credentials)
        self.assertEqual(res.status_code, 200)

    def test_delete_nonexistent(self):
        """ Tests deleting a non existent task """

        credentials = auth_header('homer', '1234')

        res = self.client.delete('/api/projects/1/tasks/3', headers=credentials)
        self.assertEqual(res.status_code, 404)

    def test_delete_from_nonexistent_project(self):
        """ Tests deleting a task from a non existent project """

        credentials = auth_header('homer', '1234')

        res = self.client.delete('/api/projects/6/tasks/1', headers=credentials)
        self.assertEqual(res.status_code, 404)