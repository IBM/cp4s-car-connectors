import json
from time import sleep

import requests
from car_framework.context import context
from car_framework.util import DatasourceFailure
from connector.data_handler import format_datetime, epoch_to_datetime_conv
from connector.error_response import ErrorResponder


class AssetServer:

    def __init__(self):

        # Get server connection arguments from config file
        with open('connector/okta_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.server = "https://" + context().args.host
        self.headers = { "Authorization" : context().args.auth_token}

    def test_connection(self):
        try:
            # datasource connection test
            server_endpoint = self.server + self.config['endpoint']['users']
            response = self.get_collection("GET", server_endpoint, headers=self.headers)
            if response.status_code == 200 and 'error' not in response.url:
                code = 0
            else:
                code = 1
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    # Pulls asset data for all collection entities
    def get_collection(self, method, server_endpoint, headers=None):
        """
        Fetch data from datasource using api
        parameters:
            method(str): REST method(GET, POST)
            server_endpoint(str): api end point
            headers(dict): http headers
        returns:
            json_data(dict): Api response
        """
        try:
            while True:
                api_response = requests.request(method, server_endpoint, headers=headers)
                # If API ratelimit exceeds sleep for one minute to resume API call
                if api_response.status_code == 429:
                    sleep(60)
                else:
                    return api_response
        except Exception as ex:
            return_obj = {}
            ErrorResponder.fill_error(return_obj, ex)
            raise Exception(return_obj)

    def get_users(self, last_model_state_id=None):
        """
        Fetch the entire asset records from data source.
        parameters:
            last_model_state_id(datetime): last run time
        returns:
            results(list): Api response
        """
        server_endpoint = self.server + self.config['endpoint']['users']
        # Incremental updates
        if last_model_state_id:
            format_time = format_datetime(last_model_state_id)
            query_filter = f'created gt "{format_time}" or lastUpdated gt "{format_time}"'
            server_endpoint = f'{server_endpoint}?search={query_filter}'
        next_records = True
        user_list = []
        # Pagination handling
        while next_records:
            response = self.get_collection("GET", server_endpoint, headers=self.headers)
            if response.status_code != 200:
                return_obj = {}
                status_code = response.status_code
                ErrorResponder.fill_error(return_obj, response.content, status_code)
                raise Exception(return_obj)
            user_list = user_list + response.json()
            if response.links.get("next"):
                server_endpoint = response.links['next']['url']
            else:
                next_records = False
        return user_list

    def get_applications(self, last_model_state_id=None):
        """
        Fetch the application records from data source.
        parameters:
            last_model_state_id(datetime): last run time
        returns:
            results(list): Api response
        """
        server_endpoint = self.server + self.config['endpoint']['apps']
        if last_model_state_id:
            format_time = format_datetime(last_model_state_id)
            query_filter = f'created gt "{format_time}" or lastUpdated gt "{format_time}"'
            server_endpoint = f'{server_endpoint}?search={query_filter}'
        app_list = []
        next_records = True
        # Pagination handling
        while next_records:
            response = self.get_collection("GET", server_endpoint, headers=self.headers)
            if response.status_code != 200:
                return_obj = {}
                status_code = response.status_code
                ErrorResponder.fill_error(return_obj, response.content, status_code)
                raise Exception(return_obj)
            app_list = app_list + response.json()
            if response.links.get("next"):
                server_endpoint = response.links['next']['url']
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
            asset_server_endpoint = f'{server_endpoint}/{app_id}/users?limit=500'
            next_records = True
            user_list = []
            # Pagination handling
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

    def get_systemlogs(self, last_model_state_id=None, event_type=None):
        """
        Fetch the event log records from data source.
        parameters:
            last_model_state_id(datetime): last run time
            event_type(string): type of the log event
        returns:
            results(list): Api response
        """
        server_endpoint = self.server + self.config['endpoint']['systemlogs']
        # Default event
        log_event_type = "user.session.start"
        if event_type:
            log_event_type = event_type

        query_params = f"?sortOrder=DESCENDING&limit=1000&filter=eventType eq \"{log_event_type}\""
        server_endpoint = server_endpoint + query_params
        if last_model_state_id:
            format_time = epoch_to_datetime_conv(last_model_state_id)
            server_endpoint = f'{server_endpoint}&since={format_time}'
        next_records = True
        system_logs = []
        while next_records:
            response = self.get_collection("GET", server_endpoint, headers=self.headers)
            if response.status_code != 200:
                return_obj = {}
                status_code = response.status_code
                ErrorResponder.fill_error(return_obj, response.content, status_code)
                raise Exception(return_obj)
            system_logs = system_logs + response.json()
            if response.links.get("next"):
                server_endpoint = response.links['next']['url']
            else:
                next_records = False
        return system_logs

    def get_users_last_login_events(self, users, logs, last_model_state_id=None):
        """
        Get the user last application login events
        parameters:
            users(list): list of users
            logs(list): list of user log-in events
            last_model_state_id(datetime): last run time
        returns:
            List of login event logs
        """
        # get complete user list in incremental import
        if last_model_state_id:
            users = self.get_users()
        user_list = [x["id"] for x in users]
        unique_events = []
        for log in logs:
            if log["actor"]["id"] in user_list:
                target1 = [app['id'] for app in log['target'] if app['type'] == 'AppInstance']
                found = False
                for event in unique_events:
                    if log["actor"]["id"] == event["actor"]["id"]:
                        target2 = [app['id'] for app in event['target'] if app['type'] == 'AppInstance']
                        if target1 == target2:
                            found = True
                            break
                if not found:
                    unique_events.append(log)

        return unique_events

    def get_asset_collections(self, last_model_state_id=None):
        """
        Fetch the entire asset collection records from data source.
        parameters:
            last_model_state_id(datetime): last run time
        returns:
            Dict of resources
        """
        user_res = self.get_users(last_model_state_id)
        application_res = self.get_applications(last_model_state_id)
        self.get_applications_users(application_res)
        logs = self.get_systemlogs(last_model_state_id)
        client_events = self.get_users_last_login_events(user_res, logs, last_model_state_id)
        collection_dict = {'user': user_res,
                           'application': application_res,
                           'client': client_events}
        return collection_dict
