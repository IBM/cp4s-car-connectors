import json
import requests
from car_framework.context import context
from car_framework.util import DatasourceFailure
from connector.error_response import ErrorResponder


class AssetServer:

    def __init__(self):

        # Get server connection arguments from config file
        with open('connector/okta_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.server = "https://" + context().args.host
        self.session = requests.session()
        self.headers = {"Authorization": "SSWS " + context().args.auth_token}

    def test_connection(self):
        try:
            # datasource connection test
            asset_server_endpoint = self.server + self.config['endpoint']['users']
            response = self.get_collection("GET", asset_server_endpoint, headers=self.headers)
            if response.status_code == 200 and 'error' not in response.url:
                code = 0
            else:
                code = 1
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    # Pulls asset data for all collection entities
    def get_collection(self, method, asset_server_endpoint, headers=None):
        """
        Fetch data from datasource using api
        parameters:
            method(str): REST method(GET, POST)
            asset_server_endpoint(str): api end point
            headers(dict): http headers
        returns:
            json_data(dict): Api response
        """
        try:
            api_response = self.session.request(method, asset_server_endpoint, headers=headers)
        except Exception as ex:
            return_obj = {}
            ErrorResponder.fill_error(return_obj, ex)
            raise Exception(return_obj)
        return api_response

    def get_assets(self):
        """
        Fetch the user records from data source.
        parameters:
        returns:
            results(list): Api response
        """
        asset_server_endpoint = self.server + self.config['endpoint']['users']
        next_records = True
        user_list = []
        while next_records:
            response = self.get_collection("GET", asset_server_endpoint, headers=self.headers)
            if response.status_code != 200:
                return_obj = {}
                status_code = response.status_code
                ErrorResponder.fill_error(return_obj, response.content, status_code)
                raise Exception(return_obj)
            user_list = user_list + response.json()
            if response.links.get("next"):
                asset_server_endpoint = response.links['next']['url']
            else:
                next_records = False
        return user_list

    def get_application(self):
        """
        Fetch the application records from data source.
        parameters:
        returns:
            results(list): Api response
        """
        asset_server_endpoint = self.server + self.config['endpoint']['apps']
        app_list = []
        next_records = True
        while next_records:
            response = self.get_collection("GET", asset_server_endpoint, headers=self.headers)
            if response.status_code != 200:
                return_obj = {}
                status_code = response.status_code
                ErrorResponder.fill_error(return_obj, response.content, status_code)
                raise Exception(return_obj)
            app_list = app_list + response.json()
            if response.links.get("next"):
                asset_server_endpoint = response.links['next']['url']
            else:
                next_records = False
        return app_list

    def get_applications_users(self, application_res):
        """
        Fetch the users associated with application from data source.
        parameters:
            application_res(list): list of applications
        returns:
            results(list): Api response
        """
        server_endpoint = self.server + self.config['endpoint']['apps']
        for app in application_res:
            app_id = app['id']
            asset_server_endpoint = f'{server_endpoint}/{app_id}/users'
            next_records = True
            user_list = []
            while next_records:
                response = self.get_collection("GET", asset_server_endpoint, headers=self.headers)
                if response.status_code != 200:
                    return_obj = {}
                    status_code = response.status_code
                    ErrorResponder.fill_error(return_obj, response.content, status_code)
                    raise Exception(return_obj)
                user_list = user_list + response.json()
                if response.links.get("next"):
                    asset_server_endpoint = response.links['next']['url']
                else:
                    next_records = False
            app['users'] = user_list
        return application_res

    def get_systemlogs(self):
        """
        Fetch the event log records from data source.
        returns:
            results(list): Api response
        """
        server_endpoint = self.server + self.config['endpoint']['systemlogs']
        # User log-in failure and success events
        query_params = "?sortOrder=ASCENDING&filter=eventType eq \"user.session.start\""
        server_endpoint = server_endpoint + query_params
        next_records = True
        system_logs = list()
        while next_records:
            response = self.get_collection("GET", server_endpoint, headers=self.headers)
            if response.status_code != 200:
                return_obj = {}
                status_code = response.status_code
                ErrorResponder.fill_error(return_obj, response.content, status_code)
                raise Exception(return_obj)
            system_logs = system_logs + response.json()
            if not response.json():
                next_records = False
            server_endpoint = response.links['next']['url']
        return system_logs
