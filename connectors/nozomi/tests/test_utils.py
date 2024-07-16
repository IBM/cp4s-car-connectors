import json
import os
from unittest.mock import patch, Mock

from car_framework.context import Context, context
from connector import full_import, server_access, inc_import
from tests import data_handler_validator


class Arguments:
    """Test args for Unit test case"""

    CONNECTION_HOST = "test.com"
    CONNECTION_PORT = 443
    CONNECTION_OPTIONS_DATA_RETENTION_PERIOD = 1
    CONFIGURATION_AUTH_KEY_NAME = "xxxxxx"
    CONFIGURATION_AUTH_KEY_TOKEN = "hjhdxxxxhfo"
    CONNECTION_NAME = "Nozomi"
    CAR_SERVICE_URL = "https://dummyapp.demo.isc.ibm"
    CAR_SERVICE_KEY = "abcdef"
    CAR_SERVICE_PASSWORD = ""
    CAR_SERVICE_URL_FOR_AUTHTOKEN = None
    CAR_SERVICE_AUTHTOKEN = None
    store_true = False
    export_data_dir = "tests/tmp/car_temp_export_data"
    keep_export_data_dir = "store_true"
    export_data_page_size = 10000
    description = "description"
    debug = None
    CONNECTOR_NAME = "nozomi"
    CONNECTOR_VERSION = '1.0'


@patch('car_framework.car_service.CarService.import_data_from_file')
@patch('car_framework.car_service.CarService.check_import_status')
def create_vertices_edges(import_obj, mock_import=None, mock_import_status=None):
    """tests for vertices and edges"""

    import_obj.data_handler.collections = {}

    # mock api's
    mock_import.return_value = Mock()
    mock_import_status.return_value = Mock()

    import_obj.import_vertices()
    import_obj.import_edges()

    actual_response = import_obj.data_handler.collections

    return actual_response


def full_import_initialization():
    """full import initialization"""
    Context(Arguments)
    context().asset_server = server_access.AssetServer()
    full_import_obj = full_import.FullImport()
    full_import_obj.new_model_state_id = 1682345211842
    return full_import_obj


def inc_import_initialization():
    """incremental import initialization"""
    Context(Arguments)
    context().asset_server = server_access.AssetServer()
    inc_import_obj = inc_import.IncrementalImport()
    return inc_import_obj


def get_response(filename, json_format=None):
    """return mock api response"""
    cur_path = os.path.dirname(__file__)
    abs_file_path = cur_path + "/mock_api/" + filename
    with open(abs_file_path, "rb") as json_file:
        response = json_file.read()
        if json_format:
            response = json.loads(response)
        return response


class NozomiMockResponse:
    """class for Okta mock api response"""

    def __init__(self, status_code, content, headers=None, text=None, url=None):
        self.status_code = status_code
        self.headers = headers
        self.text = text
        self.url = url
        self.content = content.encode('utf-8')

    def json(self):
        return json.loads(self.content.decode('utf-8'))


def validate_all_handler(actual_response):
    """validate the actual response from data handler"""

    data_handler_obj = data_handler_validator.TestConsumer()

    validations = all([data_handler_obj.handle_asset(actual_response['asset']),
                       data_handler_obj.handle_vulnerabilities(actual_response['vulnerability']),
                       data_handler_obj.handle_ipaddress(actual_response['ipaddress']),
                       data_handler_obj.handle_application(actual_response['application']),
                       data_handler_obj.handle_geo_location(actual_response['geolocation']),
                       data_handler_obj.handle_macaddress(actual_response['macaddress'])])
    return validations


class Payload(object):
    """class for converting the json response as dictionary object"""

    def __init__(self, json_data):
        self.__dict__ = json.loads(json_data)
