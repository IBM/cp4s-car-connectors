from enum import Enum
import adal
import requests
import collections
import urllib.parse
import os
import errno
import json
import traceback
import importlib
from datetime import datetime

from car_framework.context import context
from connector.data_collector import deep_get
from car_framework.util import DatasourceFailure
from car_framework.server_access import BaseAssetServer

# This is to disable context().fooMember error in IDE
# pylint: disable=no-member

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
                    context().logger.warning("WARNING: " + response.headers['Content-Type'])
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


"""Generic Error Mappings for API requests."""
class ErrorCode(Enum):
    """Error codes mappings"""
    # existing generic errors mapped
    TRANSMISSION_UNKNOWN = 'unknown'
    TRANSMISSION_CONNECT = 'service_unavailable'
    TRANSMISSION_AUTH_SSL = 'authentication_fail'
    TRANSMISSION_AUTH_CREDENTIALS = 'authentication_fail'
    TRANSMISSION_MODULE_DEFAULT_ERROR = 'unknown'
    TRANSMISSION_QUERY_PARSING_ERROR = 'invalid_query'
    TRANSMISSION_QUERY_LOGICAL_ERROR = 'invalid_query'
    TRANSMISSION_RESPONSE_EMPTY_RESULT = 'no_results'
    TRANSMISSION_SEARCH_DOES_NOT_EXISTS = 'no_results'
    TRANSMISSION_INVALID_PARAMETER = 'invalid_parameter'
    TRANSMISSION_REMOTE_SYSTEM_IS_UNAVAILABLE = 'service_unavailable'

    # azure specific errors mapped
    TRANSMISSION_SUBSCRIPTION_ERROR = 'Subscription Not Found'  # If we give invalid Subscription ID
    TRANSMISSION_BAD_REQUEST = 'Bad Request'  # start time cannot be lesser than 90 days
    TRANSMISSION_MISSING_API_VERSION = "Missing Api Version Parameter"
    TRANSMISSION_RESOURCE_NOT_FOUND = 'Resource Not Found'
    TRANSMISSION_GATEWAY_TIMEOUT = 'Gateway Timeout'
    TRANSMISSION_RESOURCE_GROUP_NOT_FOUND = 'Resource Group Not Found'

    # adal library specific errors mapped
    TRANSMISSION_UNAUTHORIZED = 'Unauthorized Client'  # If we give invalid client id
    TRANSMISSION_INVALID_CLIENT = 'Invalid Client'  # If we give invalid client secret
    TRANSMISSION_INVALID_RESOURCE = 'Invalid Resource'  # Invalid base Url
    TRANSMISSION_INVALID_REQUEST = 'Invalid Request'  # If we give invalid tenant id
    TRANSMISSION_CONNECTION_ERROR = 'HTTPS Connection Error'  # network connection error


class ErrorResponder:

    @staticmethod
    def fill_error(return_object, message_structure=None, response_code=None, message=None):
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
        caller_path_list = traceback.extract_stack()[-3].filename.split(os.path.sep)
        path_start_position = ErrorResponder.r_index(caller_path_list, 'connector')
        module_path = '.'.join(
            caller_path_list[path_start_position: -1]) + '.' 
        try:
            module = importlib.import_module(module_path)
            if json_data is not None:
                module.ErrorMapper.set_error_code(json_data, return_object)
            else:
                ErrorMapperBase.set_error_code(return_object, module.ErrorMapper.DEFAULT_ERROR)
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


class AssetServer(RestApiClient):
    """API Client to handle all calls to Azure API."""

    # common URLs
    BASE_URL = "https://management.azure.com"
    AUTHORITY_HOST_URL = "https://login.windows.net/%s/oauth2/token"
    LOGIN_URL = "https://login.microsoftonline.com/%s"

    # initial import endpoints
    VM_LIST_URL = "/subscriptions/{subscription_id}/providers/Microsoft.Compute/virtualMachines/"
    NETWORK_LIST_URL = "/subscriptions/{subscription_id}/providers/Microsoft.Network/networkInterfaces?"
    APPS_LIST_URL = "/subscriptions/{subscription_id}/providers/Microsoft.Web/sites"
    SQL_DATABASE_LIST = "/subscriptions/{subscription_id}/resourceGroups/{rg_name}/providers/Microsoft.Sql/servers/{" \
                        "server_name}/databases "
    SQL_SERVER_LIST = "/subscriptions/{subscription_id}/resourceGroups/{rg_name}/providers/Microsoft.Sql/servers"
    RESOURCE_GROUPS_LIST = "/subscriptions/{subscription_id}/resourcegroups?"
    CONTAINER_LIST_URL = "/subscriptions/{subscription_id}/providers/Microsoft.ContainerInstance/containerGroups"

    # incremental import endpoints
    ACTIVITY_LOGS_URL = "/subscriptions/{subscription_id}/providers/microsoft.insights/eventtypes/management/values"
    VM_DETAILS_URL = "/subscriptions/{subscription_id}/resourceGroups/{r_group}/providers/Microsoft.Compute" \
                     "/virtualMachines/{vm_name}"
    APP_DETAILS_URL = "/subscriptions/{subscription_id}/resourceGroups/{r_group}/providers/Microsoft.Web" \
                      "/sites/{" \
                      "app_name}"
    SQL_DB_URL = "/subscriptions/{subscription_id}/resourceGroups/{r_group}/providers/Microsoft.Sql/servers/{" \
                 "server}/databases/{db_name}"
    SQL_SERVER_URL = "/subscriptions/{subscription_id}/resourceGroups/{rg_name}/providers/Microsoft.Sql/servers/{" \
                     "server} "

    # Azure Security Center endpoint
    SECURITY_CENTER_URL = "/subscriptions/{subscription_id}/providers/Microsoft.Security/alerts"

    MAX_PAGE_NUMBER = 50

    def __init__(self):
        """Initialization."""
        RestApiClient.__init__(self, self.BASE_URL, None, None)
        self.activity_logs = None
        self.security_logs = None
        self.machine_data = None
        self.network_data = None
        self.application_data = None
        self.database_data = dict()
        self.container_data = None
        self.access_token = ""

    def test_connection(self):
        try:
            self.get_access_token()
            code = 0
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    def get_administrative_logs(self, timestamp):
        """Get the security alerts from azure management endpoint.
        :param timestamp: str, time and date for the API call
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_security(),
                '$filter': "eventTimestamp ge {timestamp} and eventTimestamp le {curr_time} and category eq "
                           "'Administrative'".format(
                               timestamp=self.epoch_to_datetime_conv(timestamp),
                               curr_time=self.epoch_to_datetime_conv(context().new_model_state_id)
                           )
            }

            header = {
                "Authorization": "Bearer " + self.get_access_token()
            }
            context().logger.info("Fetching Administrative Details from Activity Logs...")

            response = self.call_api(self.BASE_URL + self.ACTIVITY_LOGS_URL.format(
                subscription_id=self.get_subscription_id()), 'GET',
                                     headers=header, params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()
            self.activity_logs = data_json

            page = 1
            while True:
                try:
                    next_url = data_json["nextLink"]
                    if next_url is None:
                        break
                    context().logger.debug(
                        "Fetching Paginated Results of Activity Logs... Page #%s", page)
                    data_next = self.call_api(next_url, 'GET', header)
                    data_next_json = data_next.json()
                    self.activity_logs["value"].extend(data_next_json["value"])
                    data_json = data_next_json
                    page += 1
                except KeyError:
                    break
        except Exception as e:
            raise DatasourceFailure(e)

        return self.activity_logs

    def get_security_center_alerts(self, timestamp=None):
        """Get the security alerts from azure management endpoint from ASC.
        :param timestamp: str, time and date for the API call
        :return: report_data, a list of records
        """
        try:
            # params
            if timestamp:
                params_data = {
                    'api-version': self.get_api_version_security_center(),
                    '$filter': "Properties/ReportedTimeUtc lt {curr_time} and Properties/ReportedTimeUtc gt {timestamp}"
                               " and Properties/State eq 'Active'".format(
                                   timestamp=self.epoch_to_datetime_conv(timestamp),
                                   curr_time=self.epoch_to_datetime_conv(context().new_model_state_id)
                                )
                }
            else:
                params_data = {
                    'api-version': self.get_api_version_security_center(),
                    '$filter': "Properties/State eq 'Active'"
                }

            header = {
                "Authorization": "Bearer " + self.get_access_token()
            }
            context().logger.info("Fetching ASC Alerts Details from Security Center...")

            response = self.call_api(self.BASE_URL + self.SECURITY_CENTER_URL.format(
                subscription_id=self.get_subscription_id()), 'GET',
                                     headers=header, params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()
            self.security_logs = data_json

            page = 1
            while True:
                try:
                    next_url = data_json["nextLink"]
                    if next_url is None:
                        break
                    context().logger.debug(
                        "Fetching  Results of security center Logs... Page #%s", page)
                    data_next = self.call_api(next_url, 'GET', header)
                    data_next_json = data_next.json()
                    self.security_logs["value"].extend(data_next_json["value"])
                    data_json = data_next_json
                    page += 1
                except KeyError:
                    break
        except Exception as e:
            raise DatasourceFailure(e)

        return self.security_logs

    def get_virtual_machine_details(self, resource_id=None, incremental=True):
        """Get the vm details for alerts from azure management endpoint.
        :param resource_id: dict, processed data from previous API call
        :return: responses, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_vm(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }

            context().logger.debug("Fetching VM Details...")

            if not incremental:
                resource_id = self.VM_LIST_URL
                context().logger.info("Fetching List of VM Details...")

            response = self.call_api(self.BASE_URL + resource_id.format(subscription_id=self.get_subscription_id()),
                                     'GET',
                                     headers=header,
                                     params=params_data)
            data = self.handle_errors(response, {})

            data_json = data.json()
            self.machine_data = data_json

            page = 1
            while True:
                try:
                    next_url = data_json["nextLink"]
                    if next_url is None:
                        break
                    context().logger.info("Fetching Paginated Results of Virtual Machines... Page #%s", page)
                    data_next = self.call_api(next_url, 'GET', header)
                    data_next_json = data_next.json()
                    self.machine_data["value"].extend(data_next_json["value"])
                    data_json = data_next_json
                    page += 1
                except KeyError:
                    break

        except Exception as e:
            raise DatasourceFailure(e)

        return self.machine_data

    def get_virtual_machine_details_by_name(self, vm_name, r_group):
        """Get the vm details for alerts from azure management endpoint.
        :param vm_name: dict, processed data from previous API call
        :param r_group: str, resource group name
        :return: responses, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_vm(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }

            context().logger.debug("Fetching VM Details...")

            response = self.call_api(
                self.BASE_URL + self.VM_DETAILS_URL.format(subscription_id=self.get_subscription_id(), vm_name=vm_name,
                                                           r_group=r_group), 'GET', headers=header, params=params_data)
            data = self.handle_errors(response, {})

            data_json = data.json()

        except Exception as e:
            raise DatasourceFailure(e)

        return data_json

    def get_network_profile(self, network_url=None, incremental=True):
        """Get the network related details from azure management endpoint.
        :param network_url: str, endpoint of network profile API call
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_vm(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }

            if not incremental:
                network_url = self.NETWORK_LIST_URL
                context().logger.info("Fetching List of Network Interface Details...")

            context().logger.debug("Fetching Network Profile Details...")
            response = self.call_api(self.BASE_URL + network_url.format(subscription_id=self.get_subscription_id()),
                                     'GET', headers=header, params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()
            self.network_data = data_json

            page = 1
            while True:
                try:
                    next_url = data_json["nextLink"]
                    if next_url is None:
                        break
                    context().logger.info(
                        "Fetching Paginated Results of Network Profile... Page #%s", page)
                    data_next = self.call_api(next_url, 'GET', header)
                    data_next_json = data_next.json()
                    self.network_data["value"].extend(data_next_json["value"])
                    data_json = data_next_json
                    page += 1
                except KeyError:
                    break

        except Exception as e:
            raise DatasourceFailure(e)

        return self.network_data

    def get_public_ipaddress(self, network_public_ipaddr_url):
        """Get the network public ipaddress related details from azure management endpoint.
        :param network_public_ipaddr_url: str, endpoint of network profile API call
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_public_ipaddr(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }
            context().logger.debug("Fetching Network public ipaddress Details...")
            response = self.call_api(self.BASE_URL + network_public_ipaddr_url, 'GET', headers=header,
                                     params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()

        except Exception as e:
            raise DatasourceFailure(e)

        return data_json

    def get_security_logs(self, timestamp):
        """Get the security alerts from azure management endpoint.
        :param timestamp: str, time and date for the API call
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_security(),
                '$filter': "eventTimestamp ge {timestamp} and eventTimestamp le {curr_time} and category eq "
                           "'Security' and status eq 'Active'".format(
                               timestamp=self.epoch_to_datetime_conv(timestamp),
                               curr_time=self.epoch_to_datetime_conv(context().new_model_state_id)
                            )
            }

            header = {
                "Authorization": "Bearer " + self.get_access_token()
            }
            context().logger.info("Fetching Security Alert Logs...")

            response = self.call_api(self.BASE_URL + self.ACTIVITY_LOGS_URL.format(
                subscription_id=self.get_subscription_id()), 'GET',
                                     headers=header, params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()
            self.security_logs = data_json

            page = 1
            while True:
                try:
                    next_url = data_json["nextLink"]
                    if next_url is None:
                        break
                    context().logger.debug("Fetching Paginated Security Details from Activity Logs...Page # %s", page)
                    data_next = self.call_api(next_url, 'GET', header)
                    data_next_json = data_next.json()
                    self.security_logs["value"].extend(data_next_json["value"])
                    data_json = data_next_json
                    page += 1
                except KeyError:
                    break
        except Exception as e:
            raise DatasourceFailure(e)

        return self.security_logs

    def get_application_details(self, application_url=None, incremental=True):
        """Get the application related details from azure management endpoint.
        :param application_url: str, endpoint of application service API call
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_app(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }

            if not incremental:
                application_url = self.APPS_LIST_URL
                context().logger.info("Fetching list of App Services Details...")

            context().logger.debug("Fetching application Details...")

            response = self.call_api(self.BASE_URL + application_url.format(subscription_id=self.get_subscription_id()),
                                     'GET', headers=header, params=params_data)
            data = self.handle_errors(response, {})

            data_json = data.json()
            self.application_data = data_json

            page = 1
            while True:
                try:
                    next_url = data_json["nextLink"]
                    if next_url is None:
                        break
                    context().logger.info(
                        "Fetching Paginated Results of Application Data... Page #%s", page)
                    data_next = self.call_api(next_url, 'GET', header)
                    data_next_json = data_next.json()
                    self.application_data["value"].extend(data_next_json["value"])
                    data_json = data_next_json
                    page += 1
                except KeyError:
                    break

        except Exception as e:
            raise DatasourceFailure(e)

        return self.application_data

    def get_application_details_by_name(self, application_name, r_group):
        """Get the specific application related details from azure management endpoint.
        :param application_name: str, application name to fetch details
        :param r_group: str, resource group name
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_database(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }

            context().logger.info("Fetching specific application Details...")

            response = self.call_api(
                self.BASE_URL + self.APP_DETAILS_URL.format(subscription_id=self.get_subscription_id(), r_group=r_group,
                                                            app_name=application_name),
                'GET',
                headers=header,
                params=params_data)
            data = self.handle_errors(response, {})

            data_json = data.json()

        except Exception as e:
            raise DatasourceFailure(e)

        return data_json

    def get_sql_database_details(self, database_url=None):
        """Get the database related details from azure management endpoint.
        :param database_url: str, endpoint of database API call
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_database(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token()),
                "Accept": "application/json"
            }
            context().logger.debug("Fetching SQL Database Details...")

            response = self.call_api(self.BASE_URL + database_url.format(subscription_id=self.get_subscription_id()),
                                     'GET', headers=header, params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()

            if "error" not in data_json:
                # obtain related server details
                url_data = data_json.get('id', {}).split('/')
                r_group, server = url_data[4], url_data[8]
                if r_group and server:
                    server_data = self.get_sql_server_by_name(r_group, server)
                    data_json["server_map"] = server_data

        except Exception as e:
            raise DatasourceFailure(e)

        return data_json

    def get_sql_database_details_by_name(self, database_name, server, r_group):
        """Get the database related details from azure management endpoint.
        :param database_name: str, database name to make API call
        :param server: str, server name of associated database
        :param r_group: str, resource group
        :return: data_json, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_database(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token()),
                "Accept": "application/json"
            }
            context().logger.debug("Fetching SQL Database Details...")

            response = self.call_api(
                self.BASE_URL + self.SQL_DB_URL.format(subscription_id=self.get_subscription_id(), r_group=r_group,
                                                       server=server, db_name=database_name), 'GET', headers=header,
                params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()

        except Exception as e:
            raise DatasourceFailure(e)

        return data_json

    def get_all_sql_databases(self):
        """Get the database related details from azure management endpoint.
        :return: report_data, a list of records
        """
        try:
            self.database_data["value"] = []

            # params
            params_data = {
                'api-version': self.get_api_version_database(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token()),
                "Accept": "application/json"
            }
            context().logger.info("Fetching All SQL Database Details...")

            resource_groups = self.get_resource_groups()
            if "value" in resource_groups:
                for resource_group in resource_groups["value"]:
                    servers = self.get_sql_servers(resource_group["name"])
                    if len(servers["value"]) > 0:
                        for server in servers["value"]:
                            response = self.call_api(self.BASE_URL + self.SQL_DATABASE_LIST.format(
                                subscription_id=self.get_subscription_id(), rg_name=resource_group["name"],
                                server_name=server["name"]), 'GET', headers=header, params=params_data)
                            data = self.handle_errors(response, {})
                            data_json = data.json()
                            for database in data_json['value']:
                                database["server_map"] = server
                            self.database_data["value"].extend(data_json["value"])

        except Exception as e:
            raise DatasourceFailure(e)
        return self.database_data

    # def get_container_details(self, container_url=None, incremental=True):
    #     """Get the container related details from azure management endpoint.
    #     :param container_url: str, endpoint of container groups  API call
    #     :return: report_data, a list of records
    #     """
    #     try:
    #         # params
    #         params_data = {
    #             'api-version': self.get_api_version_container(),
    #         }
    #
    #         header = {
    #             "Authorization": "Bearer {}".format(self.get_access_token())
    #         }
    #
    #         if not incremental:
    #             container_url = self.CONTAINER_LIST_URL
    #
    #         context().logger.info("Fetching Container Details...")
    #
    #         response = self.call_api(self.BASE_URL + container_url.format(subscription_id=self.get_subscription_id()),
    #                                  'GET', headers=header, params=params_data)
    #         data = self.handle_errors(response, {})
    #         data_json = data.json()
    #         self.container_data = data_json
    #
    #         page = 1
    #         while True:
    #             try:
    #                 next_url = data_json["nextLink"]
    #                 if next_url is None:
    #                     break
    #                 context().logger.info("Fetching Paginated Results of Container details... Page #%s", page)
    #                 data_next = self.call_api(next_url, 'GET', header)
    #                 data_next_json = data_next.json()
    #                 self.container_data["value"].extend(data_next_json["value"])
    #                 data_json = data_next_json
    #                 page += 1
    #             except KeyError:
    #                 break
    #
    #     except Exception as e:
    #         raise DatasourceFailure(e)
    #
    #     return self.container_data

    def get_resource_groups(self):
        """Get the resource groups under an azure subscription account.
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_vm(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token())
            }
            context().logger.debug("Fetching Resource groups...")
            response = self.call_api(
                self.BASE_URL + self.RESOURCE_GROUPS_LIST.format(subscription_id=self.get_subscription_id()), 'GET',
                headers=header,
                params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()

        except Exception as e:
            raise DatasourceFailure(e)

        return data_json

    def get_sql_servers(self, r_group):
        """Get the sql servers under an azure resource group.
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_database(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token()),
                "Accept": "application/json"
            }
            context().logger.debug("Fetching SQL server Details...")
            response = self.call_api(
                self.BASE_URL + self.SQL_SERVER_LIST.format(subscription_id=self.get_subscription_id(),
                                                            rg_name=r_group), 'GET', headers=header,
                params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()

        except Exception as e:
            raise DatasourceFailure(e)

        return data_json

    def get_sql_server_by_name(self, r_group, server):
        """Get the specified sql server under an azure resource group.
        :return: report_data, a list of records
        """
        try:
            # params
            params_data = {
                'api-version': self.get_api_version_database(),
            }

            header = {
                "Authorization": "Bearer {}".format(self.get_access_token()),
                "Accept": "application/json"
            }
            context().logger.debug("Fetching specific SQL server Details...")
            response = self.call_api(
                self.BASE_URL + self.SQL_SERVER_URL.format(subscription_id=self.get_subscription_id(),
                                                           rg_name=r_group, server=server), 'GET', headers=header,
                params=params_data)
            data = self.handle_errors(response, {})
            data_json = data.json()

        except Exception as e:
            raise DatasourceFailure(e)

        return data_json

    @staticmethod
    def get_api_version_security():
        """Get access token.
        :return: str, api_version
        """
        api_version = "2015-04-01"
        return api_version

    @staticmethod
    def get_api_version_security_center():
        """Get security center api version.
        :return: str, api_version
        """
        api_version = "2019-01-01"
        return api_version

    @staticmethod
    def get_api_version_vm():
        """Get access token.
        :return: str, api_version
        """
        api_version = "2018-06-01"
        return api_version

    @staticmethod
    def get_api_version_database():
        """Get access token.
        :return: str, api_version
        """
        api_version = "2014-01-01"
        return api_version

    @staticmethod
    def get_api_version_app():
        """Get access token.
        :return: str, api_version
        """
        api_version = "2015-04-01"
        return api_version

    @staticmethod
    def get_api_version_public_ipaddr():
        """Get network public ipaddress.
        :return: str, api_version
        """
        api_version = "2018-11-01"
        return api_version

    @staticmethod
    def get_api_version_container():
        """Get container api version.
        :return: str, api_version
        """
        api_version = "2018-10-01"
        return api_version

    def get_subscription_id(self):
        """Get subscription id.
        :return: str, subscription id
        """
        subscription_id = context().args.subscription_id
        return subscription_id

    def get_access_token(self): 
        """This function is use to get bearer token using app secret,client Id and tenant
        :param: clientID,resource, clientSecret and redirect_url
        :return: bearerToken
        """
        url = self.LOGIN_URL % context().args.tenantID

        try:
            authContext = adal.AuthenticationContext(
                url, validate_authority=context().args.tenantID != 'ADFS',
            )
            token = authContext.acquire_token_with_client_credentials(
                self.BASE_URL,
                context().args.clientID,
                context().args.clientSecret)
            self.access_token = token['accessToken']

            return self.access_token

        except Exception as ex:
            error = ErrorResponder.fill_error({}, ex)
            raise DatasourceFailure(error)

    @staticmethod
    def epoch_to_datetime_conv(epoch_time):
        epoch_time = float(epoch_time) / 1000.0
        datetime_time = datetime.fromtimestamp(epoch_time)
        
        utc_format_string = "{date_part}T{time_part}Z"
        utc_list = str(datetime_time).split()
        return utc_format_string.format(date_part=utc_list[0], time_part=utc_list[1])

    @staticmethod
    def handle_errors(response, return_obj):
        """This function is use to check the response code"""
        response_code = response.status_code
        response_txt = response.text

        if 200 <= response_code < 300:
            return response
        if response_code == 404 and deep_get(json.loads(response_txt), ["error", "code"]) in ["ResourceNotFound",
                                                                                              "ResourceGroupNotFound"]:
            return response
        elif ErrorResponder.is_plain_string(response_txt):
            ErrorResponder.fill_error(return_obj, message=response_txt)
            raise Exception(return_obj)
        elif ErrorResponder.is_json_string(response_txt):
            response_json = json.loads(response_txt)
            ErrorResponder.fill_error(return_obj, response_json, response_code, )
            raise Exception(return_obj)
        else:
            raise Exception(return_obj)