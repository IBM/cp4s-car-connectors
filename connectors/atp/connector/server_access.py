import adal
import json
import requests
import sys
import collections
import urllib.parse
import os
import errno
from enum import Enum
import traceback
import importlib

from car_framework.context import context
from car_framework.util import DatasourceFailure
from car_framework.server_access import BaseAssetServer

# This is to disable context().fooMember error in IDE
# pylint: disable=no-member

""""REST API Client for handling API requests."""

# This is a simple HTTP client that can be used to access the REST API
class RestApiClient(BaseAssetServer):
    def __init__(self, host, port=None, cert=None, headers={}, url_modifier_function=None, cert_verify=True):
        server_ip = host
        if port is not None:
            server_ip += ":" + str(port)
        self.server_ip = server_ip
        self.cert_verify = str(cert_verify).lower() not in ['0', 'f', 'false', 'f', 'n', 'no', 'disable', 'disabled']
        self.cert = cert
        self.headers = headers
        self.url_modifier_function = url_modifier_function

    # This method is used to set up an HTTP request and send it to the server
    def call_api(self, endpoint, method, headers=None, data=None, params=[], urldata=None):

        self.cert_file_name = None
        try:
            if self.cert is not None and self.cert_verify:
                # put key/cert pair into a file to read it later
                self.cert_file_name = "cert.pem"
                with open(self.cert_file_name, 'w') as f:
                    try:
                        f.write(self.cert)
                    except IOError:
                        context().logger.error('Failed to setup certificate')

            actual_headers = self.headers.copy()
            if headers is not None:
                for header_key in headers:
                    actual_headers[header_key] = headers[header_key]

            actual_headers["Content-Type"] = "application/json"

            if urldata is not None:
                urldata = urllib.parse.urlencode(urldata)
                if '?' in endpoint:
                    endpoint += '&'
                else:
                    endpoint += '?'
                endpoint += urldata

            if self.url_modifier_function is not None:
                url = self.url_modifier_function(self.server_ip, endpoint, actual_headers)
            else:
                url = endpoint
            try:

                call = getattr(requests, method.lower())
                response = call(url, headers=actual_headers, cert=self.cert_file_name, data=data,
                                verify=self.cert_verify, params=params)

                if 'headers' in dir(response) and isinstance(response.headers,
                                                             collections.Mapping) and 'Content-Type' in response.headers \
                        and "Deprecated" in response.headers['Content-Type']:
                    context().logger.warning("WARNING: " + response.headers['Content-Type'], file=sys.stderr)
                return response
            except Exception as e:
                context().logger.error('exception occurred during requesting url: ' + str(e))
                raise e
        finally:
            if self.cert_file_name is not None:
                try:
                    os.remove(self.cert_file_name)
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise

    # Simple getters that can be used to inspect the state of this client.
    def get_headers(self):
        return self.headers.copy()

    def get_server_ip(self):
        return self.server_ip

class AssetServer(RestApiClient):
    """API Client to handle all calls to Microsoft Windows Defender ATP API."""

    # common URLs
    LOGIN_URL = "https://login.microsoftonline.com/%s"
    BASE_URL = "https://api.securitycenter.windows.com"
    MACHINE_LIST_URL = "/api/machines"
    ALERT_URL = "/api/alerts"
    ADVANCED_HUNTING_URL = "/api/advancedqueries/run/"
    MAC_PRIVATE_IP_QUERY = "DeviceNetworkInfo | where DeviceId in {machine_id} and Timestamp >= ago(30d) and " \
                           "IPAddresses contains 'Private'| order by Timestamp desc | distinct DeviceId, " \
                           "IPAddresses, MacAddress, DeviceName"
    MAC_PRIVATE_IP_INC = "DeviceNetworkInfo | where DeviceId in {machine_id} and Timestamp >= datetime({last_run}) " \
                         "and Timestamp < datetime({current_run}) and IPAddresses contains 'Private'| order by " \
                         "Timestamp desc | distinct DeviceId, IPAddresses, MacAddress, DeviceName"
    USERS_URL = "/api/machines/{id}/logonusers"
    VULNERABILITY_QUERY = "DeviceTvmSoftwareVulnerabilities | where DeviceId in {machine_id} | join kind = " \
                          "leftouter(DeviceTvmSoftwareVulnerabilitiesKB) on CveId"

    def __init__(self, response_handler=None, default_headers=None):
        """Initialization."""
        RestApiClient.__init__(self, self.BASE_URL, response_handler, default_headers)
        self.machine_list = None
        self.alerts_list = None
        self.mac_private_ip = None
        self.user_list = None
        self.vuln_details = None
        self.access_token = ""

    def test_connection(self):
        try:
            self.get_machine_list()
            code = 0
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    def get_machine_list(self, timestamp=None, curr_time=None, delete=None):
        """Get the machine details from ms-atp endpoint.
            :param timestamp: string, Timestamp for incremental update
            :param delete: string, Timestamp for delete asset
            :return: responses, a list of records
        """
        try:
            # params
            if timestamp and curr_time:
                params_data = {
                    'api-version': self.get_api_version_vm(),
                    '$filter': "lastSeen ge {timestamp} and lastSeen le {curr_time}".format(
                        timestamp=timestamp, curr_time=curr_time)}
            elif delete:
                params_data = {
                    'api-version': self.get_api_version_vm(),
                    '$filter': "lastSeen le {timestamp} and healthStatus eq 'Inactive'".format(
                        timestamp=delete)}
            else:
                params_data = {
                    'api-version': self.get_api_version_vm(),
                }
            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }

            response = self.call_api(self.BASE_URL + self.MACHINE_LIST_URL, 'GET', header, params=params_data)
            data = self.handle_errors(response, {})
            self.machine_list = data.json()

        except Exception as e:
            raise DatasourceFailure(e.args[0])

        return self.machine_list

    def get_alerts_list(self, incremental=False):
        """Get the  alerts from msatp endpoint.
            :param incremental: bool, flag
            :return: report_data, a list of records
        """
        try:
            # params
            if incremental:
                params_data = {
                    'api-version': self.get_api_version_vm(),
                    '$filter': "status eq 'New' or status eq 'InProgress' or status eq 'Resolved'"
                    }

            else:
                params_data = {
                    'api-version': self.get_api_version_vm(),
                    '$filter': "status eq 'New' or status eq 'InProgress'"
                }
            header = {
                "Authorization": "Bearer " + self.get_access_token()
            }

            response = self.call_api(self.BASE_URL + self.ALERT_URL, 'GET', header, params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()
            self.alerts_list = data_json

        except Exception as e:
            raise DatasourceFailure(e.args[0])

        return self.alerts_list

    def mac_private_ip_information(self, incremental,  machine_id, last_run=None, current_run=None):
        """Get the network private ip address related details from ms-atp endpoint.
           :param machine_id: str, asset id for network profile API call
           :param incremental : bool incremental
           :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_vm(),
            }

            header = {
                "Authorization": "Bearer " + self.get_access_token()
            }
            query_expression = None
            if not incremental:
                query_expression = json.dumps({'Query': self.MAC_PRIVATE_IP_QUERY.format(machine_id=machine_id)}).\
                    encode("utf-8")
            else:
                query_expression = json.dumps({'Query': self.MAC_PRIVATE_IP_INC.format(last_run=last_run,
                                    current_run=current_run, machine_id=machine_id)}).encode("utf-8")

            response = self.call_api(self.BASE_URL + self.ADVANCED_HUNTING_URL, 'POST',
                                     header, params=params_data, data=query_expression)

            data = self.handle_errors(response, {})
            data_json = data.json()
            self.mac_private_ip = data_json

        except Exception as e:
            raise DatasourceFailure(e.args[0])

        return self.mac_private_ip

    def get_user_information(self, machine_id):
        """Get the user related details from ms-atp endpoint.
           :param machine_id: str, asset id for user profile API call
           :return: report_data, a list of records
        """
        try:

            params_data = {
                'api-version': self.get_api_version_vm(),
            }
            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }

            response = self.call_api(self.BASE_URL + self.USERS_URL.format(id=machine_id), 'GET',
                                     header, params=params_data)

            data = self.handle_errors(response, {})
            self.user_list = data.json()

        except Exception as e:
            raise DatasourceFailure(e.args[0])

        return self.user_list

    def vulnerability_information(self, machine_id):
        """Get the vulnerability related details from ms-atp endpoint.
           :param machine_id: str, asset id for vulnerability API call
           :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_vm(),
            }

            header = {
                "Authorization": "Bearer " + self.get_access_token()
            }
            query_expression = json.dumps({'Query': self.VULNERABILITY_QUERY.format(machine_id=machine_id)}). \
                encode("utf-8")
            response = self.call_api(self.BASE_URL + self.ADVANCED_HUNTING_URL, 'POST',
                                     header, params=params_data, data=query_expression)
            data = self.handle_errors(response, {})
            data_json = data.json()
            self.vuln_details = data_json

        except Exception as e:
            raise DatasourceFailure(e.args[0])

        return self.vuln_details

    @staticmethod
    def get_api_version_vm():
        """Get access token.
        :return: str, api_version
        """
        api_version = "v1.0"
        return api_version

    def get_access_token(self):
        """This function is use to get bearer token using app secret,client Id and tenant
        :param: client_id,resource, client_secret and redirect_url
        :return: bearerToken
        """
        url = self.LOGIN_URL % context().args.tenantID

        try:
            authContext = adal.AuthenticationContext(
                url, validate_authority=context().args.tenantID != 'ADFS', )
            token = authContext.acquire_token_with_client_credentials(
                self.BASE_URL,
                context().args.clientID,
                context().args.clientSecret)
            self.access_token = token['accessToken']
            return self.access_token

        except Exception as ex:
            error = ErrorResponder.fill_error({}, ex)
            raise Exception(error)

    @staticmethod
    def handle_errors(response, return_obj):
        """This function is use to check the response code"""
        response_code = response.status_code
        response_txt = response.text

        if 200 <= response_code < 300:
            return response
        elif ErrorResponder.is_plain_string(response_txt):
            ErrorResponder.fill_error(return_obj, message=response_txt, response_code=response_code)
            raise Exception(return_obj)
        elif ErrorResponder.is_json_string(response_txt):
            response_json = json.loads(response_txt)
            ErrorResponder.fill_error(return_obj, response_json, response_code, )
            raise Exception(return_obj)
        else:
            raise Exception(return_obj)


"""Generic Error Mappings for API requests."""
class ErrorCode(Enum):
    """Error codes mappings"""
    # existing generic errors mapped
    TRANSMISSION_UNKNOWN = 'unknown'
    TRANSMISSION_AUTH_CREDENTIALS = 'authentication_fail'
    TRANSMISSION_MODULE_DEFAULT_ERROR = 'unknown'
    TRANSMISSION_QUERY_PARSING_ERROR = 'invalid_query'
    TRANSMISSION_SEARCH_DOES_NOT_EXISTS = 'no_results'
    TRANSMISSION_INVALID_PARAMETER = 'invalid_parameter'
    TRANSMISSION_REMOTE_SYSTEM_IS_UNAVAILABLE = 'service_unavailable'

    # msatp specific errors mapped
    TRANSMISSION_SUBSCRIPTION_ERROR = 'Subscription Not Found'
    TRANSMISSION_BAD_REQUEST = 'Bad Request'
    TRANSMISSION_MISSING_API_VERSION = "Missing Api Version Parameter"
    TRANSMISSION_RESOURCE_NOT_FOUND = 'Resource Not Found'
    TRANSMISSION_GATEWAY_TIMEOUT = 'Gateway Timeout'
    TRANSMISSION_RESOURCE_GROUP_NOT_FOUND = 'Resource Group Not Found'

    # adal library specific errors mapped
    TRANSMISSION_UNAUTHORIZED = 'Unauthorized Client'
    TRANSMISSION_INVALID_CLIENT = 'Invalid Client'
    TRANSMISSION_INVALID_RESOURCE = 'Invalid Resource'
    TRANSMISSION_INVALID_REQUEST = 'Invalid Request'
    TRANSMISSION_CONNECTION_ERROR = 'HTTPS Connection Error'


class ErrorResponder:

    @staticmethod
    def fill_error(return_object, message_structure=None, response_code=None, message=None):
        structure_map = None
        return_object['success'] = False

        if response_code:
            return_object['status_code'] = response_code
        elif "error_response" in message_structure.__dir__():
            return_object['status_code'] = message_structure.error_response.get('error_codes')
        else:
            return_object['status_code'] = 'unknown'

        error_code = ErrorCode.TRANSMISSION_UNKNOWN

        if message is None:
            message = ''

        if message_structure:
            if "error_response" in message_structure.__dir__():
                structure_map = message_structure.error_response
            elif 'args' in message_structure.__dir__():
                structure_map = message_structure.args
            else:
                structure_map = message_structure

            message += str(structure_map)

        if message is not None and message:
            if error_code.value == ErrorCode.TRANSMISSION_UNKNOWN.value:
                if 'uthenticat' in message or 'uthoriz' in message:
                    error_code = ErrorCode.TRANSMISSION_AUTH_CREDENTIALS
                elif 'query_syntax_error' in message:
                    error_code = ErrorCode.TRANSMISSION_QUERY_PARSING_ERROR
            return_object['message'] = str(message)
        ErrorMapperBase.set_error_code(return_object, error_code.value)
        if error_code == ErrorCode.TRANSMISSION_UNKNOWN:
            ErrorResponder.call_module_error_mapper(structure_map, return_object)
        
        return return_object

    @staticmethod
    def call_module_error_mapper(json_data, return_object):
        try:
            if json_data is not None:
                ErrorMapper.set_error_code(json_data, return_object)
            else:
                ErrorMapperBase.set_error_code(return_object, ErrorMapper.DEFAULT_ERROR)
        except ModuleNotFoundError:
            pass

    @staticmethod
    def r_index(my_list, my_value):
        return len(my_list) - my_list[::-1].index(my_value) - 1

    @staticmethod
    def is_plain_string(s):
        return isinstance(s, str) and not s.startswith('<?') and not s.startswith('{')

    @staticmethod
    def is_json_string(s):
        return isinstance(s, str) and s.startswith('{')


class ErrorMapperBase:
    @staticmethod
    def set_error_code(return_obj, code, message=None):
        if isinstance(code, Enum):
            return_obj['error_type'] = code.value
        else:
            return_obj['error_type'] = code
        if message is not None:
            return_obj['error'] = message

        return return_obj

""" Microsoft Windows Defender ATP Connector Specific Error Handling"""


ERROR_MAPPING = {
    "json_parse_exception": ErrorCode.TRANSMISSION_QUERY_PARSING_ERROR,
    "illegal_argument_exception": ErrorCode.TRANSMISSION_INVALID_PARAMETER,
    "SubscriptionNotFound": ErrorCode.TRANSMISSION_SUBSCRIPTION_ERROR,
    "ResourceNotFound": ErrorCode.TRANSMISSION_RESOURCE_NOT_FOUND,
    "invalid_resource": ErrorCode.TRANSMISSION_REMOTE_SYSTEM_IS_UNAVAILABLE,
    "unauthorized_client": ErrorCode.TRANSMISSION_UNAUTHORIZED,
    "NotFound": ErrorCode.TRANSMISSION_SEARCH_DOES_NOT_EXISTS,
    "BadRequest": ErrorCode.TRANSMISSION_BAD_REQUEST,
    "invalid_request": ErrorCode.TRANSMISSION_INVALID_RESOURCE,
    "HTTPSConnectionError": ErrorCode.TRANSMISSION_CONNECTION_ERROR,
    "invalid_client": ErrorCode.TRANSMISSION_INVALID_CLIENT,
    "MissingApiVersionParameter": ErrorCode.TRANSMISSION_MISSING_API_VERSION,
    "GatewayTimeout": ErrorCode.TRANSMISSION_GATEWAY_TIMEOUT,
    "ResourceGroupNotFound": ErrorCode.TRANSMISSION_RESOURCE_GROUP_NOT_FOUND,
    "InvalidSubscriptionId": ErrorCode.TRANSMISSION_SUBSCRIPTION_ERROR,
    "MissingSubscription": ErrorCode.TRANSMISSION_SUBSCRIPTION_ERROR,
    "NoRegisteredProviderFound": ErrorCode.TRANSMISSION_INVALID_RESOURCE,
}


class ErrorMapper:
    """"ErrorMapper class"""
    DEFAULT_ERROR = ErrorCode.TRANSMISSION_MODULE_DEFAULT_ERROR

    @staticmethod
    def set_error_code(json_data, return_obj):
        """Microsoft Windows Defender ATP transmit specified error
         :param json_data: dict, error response of api_call
         :param return_obj: dict, returns error and error code"""

        error_type = ''
        if isinstance(json_data, tuple):
            if str(json_data).__contains__('HTTPSConnectionError') \
                    or str(json_data).__contains__('HTTPSConnectionPool'):
                error_type = 'HTTPSConnectionError'
        elif json_data.get('error'):
            if 'code' in json_data.get('error'):
                error_type = json_data['error']['code']
            elif 'error' in json_data:
                error_type = json_data.get('error')
        elif json_data.get('Code'):
            error_type = json_data.get('Code')

        else:
            error_type = 'unknown'

        error_code = ErrorMapper.DEFAULT_ERROR

        if error_type in ERROR_MAPPING:
            error_code = ERROR_MAPPING.get(error_type)

        # if error_code == ErrorMapper.DEFAULT_ERROR:
        #     print("failed to map: " + str(json_data))

        ErrorMapperBase.set_error_code(return_obj, error_code)
        return return_obj