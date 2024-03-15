import json
import requests
from car_framework.context import context
from car_framework.util import DatasourceFailure

# Page limits
PAGE_SIZE = 10000


class AssetServer:

    def __init__(self):
        # Get server connection arguments from config file
        with open('connector/nozomi_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.base_url = f"https://{context().args.CONNECTION_HOST}:{context().args.CONNECTION_PORT}"
        if context().args.CONNECTION_HOST.startswith("http"):
            self.base_url = f"{context().args.CONNECTION_HOST}:{context().args.CONNECTION_PORT}"
        self.auth = {"key_name": context().args.CONFIGURATION_AUTH_KEY_NAME,
                     "key_token": context().args.CONFIGURATION_AUTH_KEY_TOKEN
                     }
        self.session = requests.session()
        self.headers = {'Content-Type': 'application/json'}

    # Pulls asset data for all collection entities
    def get_collection(self, method, asset_server_endpoint, data={}, headers=None):
        """
        Fetch data from datasource using api
        parameters:
            method(str): REST methode(GET, POST)
            asset_server_endpoint(str): api end point
            data(str): api input
            headers(dict): Request headers
        returns:
            api_response: Api response
        """
        try:
            api_response = self.session.request(method, asset_server_endpoint,
                                                data=data, headers=headers)
        except Exception as ex:
            raise DatasourceFailure(ex)

        return api_response

    def get_bearer_token(self):
        """Generate bearer token from API key"""
        server_endpoint = self.base_url + self.config['sign_in']['endpoint']
        response = self.get_collection("POST", server_endpoint, data=self.auth)
        if response.status_code != 200:
            try:
                error_details = response.json()
            except json.JSONDecodeError:
                error_details = response.text
            if response.status_code == 404:
                error_details = f"Requested url is invalid : {response.url}"
            elif error_details.get('errors') and 'key_name' in error_details.get('errors').keys():
                error_details = "Invalid key_name or key_token"
            raise DatasourceFailure(error_details, response.status_code)
        return response.headers.get("Authorization")

    def test_connection(self):
        """test the connection"""
        try:
            server_endpoint = self.base_url + self.config['sign_in']['endpoint']
            response = self.get_collection("POST", server_endpoint, data=self.auth)
            if response.status_code == 200:
                code = 0
            else:
                code = 1
        except Exception as e:
            context().logger.error("Test connection failed, error:%s", e)
            code = 1
        return code

    def get_query_results(self, category, query_filter=None):
        """
        Fetch the openapi query results from data source using pagination.
        parameters:
            category(str): Query item, supported values are
                            asset, sensors, nodes, asset_cves, vulnerability, software_list
            query_filter : conditional statement to filter items
        returns:
            results(list): query results list
        """
        results = []
        page = 1
        while True:
            if not self.headers.get('Authorization'):
                self.headers['Authorization'] = self.get_bearer_token()
            url = self.base_url + self.config[category]['endpoint']
            if query_filter:
                url = f'{url} | {query_filter}'
            # The default application response doesn't have asset_id field,
            # select specific fields required for CAR implementation.
            if 'fields' in self.config[category]:
                url = url + '| select ' + ' '.join(self.config[category]['fields'])
            # Sorting based on id and handling pagination
            url = f'{url} | sort id&page={page}&count={PAGE_SIZE}'
            response = self.get_collection("GET", url, headers=self.headers)
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = response.text
            if response.status_code == 401 and (
                    not response.content or 'Signature has expired' in response_json.get('error', {}).get('message',
                                                                                                          '')):
                context().logger.info("Authorization token Expired, requesting for new token")
                self.headers["Authorization"] = self.get_bearer_token()
                continue
            if response.status_code == 404:
                raise DatasourceFailure(f"Requested url is invalid : {response.url}", response.status_code)
            if response_json.get('error'):
                raise DatasourceFailure(response_json.get('error'))
            results.extend(response_json['result'])
            if len(response_json['result']) < PAGE_SIZE:
                break
            page += 1
        return results
