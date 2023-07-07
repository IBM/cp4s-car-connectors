import os
import json
from unittest.mock import patch, Mock
from tests import data_handler_validator
from car_framework.context import Context, context
from connector import full_import, server_access, inc_import


class Arguments:
    """Test args for Unit test case"""
    CONFIGURATION_AUTH_TOKEN = "whatever"
    CONNECTION_HOST = "demo.tanium.io"
    CONNECTION_PORT = "8443"
    CONNECTION_NAME = "tanium"
    CAR_SERVICE_URL = "https://app.demo.isc.ibm"
    CAR_SERVICE_KEY = "abcdef"
    CAR_SERVICE_PASSWORD = ""
    CAR_SERVICE_URL_FOR_AUTHTOKEN = None
    CAR_SERVICE_AUTHTOKEN = None
    store_true = False
    export_data_dir = "tests/tmp/car_temp_export_data"
    keep_export_data_dir = "store_true"
    export_data_page_size = 2000
    description = "description"
    debug = None
    CONNECTOR_NAME = "tanium"
    CONNECTOR_VERSION = '1.0'


class TaniumMockResponse:
    """class for rhacs mock api response"""

    def __init__(self, response_code, txt):
        self.status_code = response_code
        self.text = txt
        if isinstance(txt, dict):
            self.text = json.dumps(txt)

    def json(self):
        return self.text


class JsonResponse:
    """
     Summary conversion of json data to dictionary.
          """
    def __init__(self, response_code, filename):
        self.status_code = response_code
        self.filename = filename

    # def status_code(self):
    #     return self.status_code

    def json(self):
        cur_path = os.path.dirname(__file__)
        abs_file_path = os.path.join(cur_path, "mock_api", self.filename)
        json_file = open(abs_file_path)
        json_str = json_file.read()
        json_data = json.loads(json_str)
        return json_data

    def text(self):
        cur_path = os.path.dirname(__file__)
        abs_file_path = os.path.join(cur_path, "mock_api", self.filename)
        json_file = open(abs_file_path)
        json_str = json_file.read()
        return json_str

@patch('car_framework.car_service.CarService.import_data_from_file')
@patch('car_framework.car_service.CarService.check_import_status')
def create_vertices_edges(import_obj, mock_import=None, mock_import_status=None):
    """tests for vertices and edges"""

    import_obj.import_vertices()
    import_obj.import_edges()

    actual_response = import_obj.data_handler.collections

    return actual_response


def full_import_initialization():
    """full import initialization"""
    Context(Arguments)
    context().asset_server = server_access.AssetServer()
    full_import_obj = full_import.FullImport()
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


def validate_all_handler(actual_response):
    """validate the actual response from data handler"""

    data_handler_obj = data_handler_validator.TestConsumer()

    validations = all([data_handler_obj.handle_assets(actual_response),
                       data_handler_obj.handle_ipaddress(actual_response),
                       data_handler_obj.handle_hostname(actual_response),
                       data_handler_obj.handle_ports(actual_response),
                       data_handler_obj.handle_application(actual_response),
                       data_handler_obj.handle_macaddress(actual_response),
                       ])
    return validations

