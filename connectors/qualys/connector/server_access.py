import json
import requests
import xmltodict
from requests.auth import HTTPBasicAuth
from car_framework.context import context
from connector.error_response import ErrorResponder
from connector.data_handler import epoch_to_datetime_conv, append_vuln_in_asset


class AssetServer(object):

    def __init__(self):

        # Get server connection arguments from config file
        with open('connector/qualys_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.basic_auth = HTTPBasicAuth(context().args.username,
                                        context().args.password)

    # Pulls asset data for all collection entities
    def get_collection(self, asset_server_endpoint, headers=None, auth=None, data=None):
        """
        Fetch data from datasource using api
        parameters:
            asset_server_endpoint(str): api end point
            data(str): api input
        returns:
            json_data(dict): Api response
        """
        try:
            resp = requests.post(asset_server_endpoint, headers=headers,
                                 auth=auth, data=data)
        except Exception as ex:
            return_obj = {}
            ErrorResponder.fill_error(return_obj, ex)
            raise Exception(return_obj)

        return resp

    def get_assets(self, last_model_state_id=None):
        """
        Fetch the entire asset records from data source using pagination.
        parameters:
            asset_server_endpoint(str): api end point
            last_model_state_id(datetime): last run time
        returns:
            results(list): Api response
        """

        data = None
        results = []
        pagination = True
        headers = self.config['parameter']['headers']
        auth = self.basic_auth
        asset_server_endpoint = context().args.server + self.config['endpoint']['asset']

        # adding filter for incremental run
        if last_model_state_id:
            data = '<ServiceRequest>' \
                   '<filters><Criteria field="updated" operator="GREATER">%s</Criteria></filters>' \
                   '</ServiceRequest>' % last_model_state_id

        while pagination:
            response = self.get_collection(asset_server_endpoint, headers=headers, auth=auth, data=data)
            response_json = response.json()
            if response.status_code != 200 or response_json['ServiceResponse']['responseCode'] != 'SUCCESS':
                return_obj, error_msg = {}, {}
                status_code = response_json['ServiceResponse']['responseCode']
                error_msg['message'] = response_json['ServiceResponse']['responseErrorDetails']
                ErrorResponder.fill_error(return_obj, json.dumps(error_msg).encode(), status_code)
                raise Exception(return_obj)

            if response_json['ServiceResponse'].get('data'):
                results = results + response_json['ServiceResponse']['data']

            # check previous api call response hasMoreRecords
            if response_json['ServiceResponse'].get('hasMoreRecords') and \
                    response_json['ServiceResponse']['hasMoreRecords'] == 'true':

                # adding filter and pagination for incremental run
                if last_model_state_id:
                    data = '<ServiceRequest>' \
                           '<preferences><startFromOffset>%s</startFromOffset></preferences>' \
                           '<filters><Criteria field="updated" operator="GREATER">%s</Criteria></filters>' \
                           '</ServiceRequest>' % (response_json['ServiceResponse']['count'] + 1, last_model_state_id)
                else:  # adding filter and pagination for full import
                    data = '<ServiceRequest>' \
                           '<preferences><startFromOffset>%s</startFromOffset></preferences>' \
                           '</ServiceRequest>' % (response_json['ServiceResponse']['count'] + 1)
            else:
                pagination = False

        return results

    def get_vulnerabilities(self):
        """
        Fetch the entire vulnerability  records from data source using pagination.
        returns:
            results(list): Api response
        """
        data = None
        results = []
        pagination = True
        headers = self.config['parameter']['headers']
        auth = self.basic_auth
        server_endpoint = context().args.server + self.config['endpoint']['asset_vulnerability']
        while pagination:
            response = self.get_collection(server_endpoint, headers=headers, auth=auth, data=data)
            if response.status_code != 200:
                response = xmltodict.parse(response.text)
                return_obj = {}
                status_code = response['SIMPLE_RETURN']['RESPONSE']['CODE']
                error_message = response['SIMPLE_RETURN']['RESPONSE']['TEXT']
                ErrorResponder.fill_error(return_obj, error_message.encode('utf'), status_code)
                raise Exception(return_obj)
            response = xmltodict.parse(response.text)

            if response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE'].get('HOST_LIST'):
                if isinstance(response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']['HOST_LIST']['HOST'], list):
                    results = results + response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']['HOST_LIST']['HOST']
                else:
                    temp = []
                    temp.append(response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']['HOST_LIST']['HOST'])
                    results = results + temp
            # check the response has more records, will use the link.
            if 'WARNING' in response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']:
                server_endpoint = response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']['WARNING']['URL']
            else:
                pagination = False
        return results

    def get_bearer_token(self):
        """
        Generate bearer token using credentials
        :return: Bearer token
        """
        endpoint = context().args.gateway + self.config['endpoint']['auth']
        data = 'username=%s&password=%s&token=true' % (context().args.username, context().args.password)
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        response = self.get_collection(endpoint, headers=header, data=data)
        # on successful token generation 201 status code will be returned
        if response.status_code != 201:
            response_json = response.json()
            return_obj, error_msg = {}, {}
            status_code = response.status_code
            error_msg['message'] = response_json.get('message')
            ErrorResponder.fill_error(return_obj, json.dumps(error_msg).encode(), status_code)
            raise Exception(return_obj)
        return response.text

    def get_applications(self, last_model_state_id=None):
        """
        Fetch the application records from data source using pagination.
        parameters:
            last_model_state_id: last import time
        returns:
            results(list): Api response
        """

        pagination = True
        results = []
        data = None
        token = self.get_bearer_token()
        headers = {"Authorization": "Bearer %s" % token}
        asset_server_endpoint = context().args.gateway + self.config['endpoint']['applications']
        if last_model_state_id:
            asset_server_endpoint = asset_server_endpoint + '&assetLastUpdated=%s' % last_model_state_id
        server_endpoint = asset_server_endpoint
        response_json = None
        while pagination:

            response = self.get_collection(server_endpoint, headers=headers, data=data)
            if response.text:
                response_json = response.json()
                if response.status_code not in [200, 204] or response_json['responseCode'] != 'SUCCESS':
                    return_obj, error_msg = {}, {}
                    status_code = response_json['responseCode']
                    error_msg['message'] = response_json['responseErrorDetails']
                    ErrorResponder.fill_error(return_obj, json.dumps(error_msg).encode(), status_code)
                    raise Exception(return_obj)
                results = results + response_json['assetListData']['asset']

                # check previous api call response hasMoreRecords
            if response_json and response_json['hasMore']:
                server_endpoint = asset_server_endpoint + '&lastSeenAssetId=%s' % (response_json['lastSeenAssetId'])
            else:
                pagination = False
        return results

    # Get all asset and vulnerability records
    def get_model_state_delta(self, last_model_state_id, new_model_state_id):

        last_model_state_id = epoch_to_datetime_conv(last_model_state_id)

        # fetch the recent changes
        host_list = self.get_assets(last_model_state_id)

        vuln_list = self.get_vulnerabilities()
        applications = self.get_applications(last_model_state_id)

        return append_vuln_in_asset(host_list, vuln_list, applications)
