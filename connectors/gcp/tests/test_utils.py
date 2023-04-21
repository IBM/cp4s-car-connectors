import json
import os
from unittest.mock import patch, Mock

from car_framework.context import Context, context
from connector import full_import, server_access, inc_import
from tests import data_handler_validator


class Arguments:
    """Test args for Unit test case"""

    host = "test.com"
    client_email = "test@gmail.com"
    certificate = "hjhdskjfhlahlfoiewhfo"
    page_size = 10
    source = "GCP"
    car_service_apikey_url = "https://dummyapp.demo.isc.ibm"
    api_key = "abcdef"
    api_password = ""
    car_service_token_url = None
    api_token = None
    store_true = False
    export_data_dir = "tests/tmp/car_temp_export_data"
    keep_export_data_dir = "store_true"
    export_data_page_size = 10000
    description = "description"
    debug = None
    connector_name = "gcp"
    version = '1.0'


class GCPMockResponse:
    """class for GCP mock api response"""

    def __init__(self, response_code, txt):
        self.status_code = response_code
        self.content = txt
        if isinstance(txt, dict):
            self.content = json.dumps(txt)


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

    validations = all([data_handler_obj.handle_asset(actual_response['asset']),
                       data_handler_obj.handle_ipaddress(actual_response['ipaddress']),
                       data_handler_obj.handle_geo_location(actual_response['geolocation']),
                       data_handler_obj.handle_vulnerabilities(actual_response['vulnerability']),
                       data_handler_obj.handle_scc_vulnerabilities(actual_response['vulnerability'])
                       ])

    return validations


class Payload(object):
    """class for converting the json response as dictionary object"""

    def __init__(self, json_data):
        self.__dict__ = json.loads(json_data)


def project_response():
    """mocking response of project_list"""

    response = Payload(json.dumps(get_response('project_list.json', True)))
    return response


def mock_response():
    # Mock VM instance,OS and Vulnerability responses
    vm_instance = get_response('vm_instances.json', True)
    vm_instance_os_pkgs = get_response('vm_instance_os_pkgs.json', True)
    vm_instance_os_vuln = get_response('vm_instance_os_vuln.json', True)
    web_app = get_response('web_app.json', True)
    web_app_service = get_response('web_app_service.json', True)
    web_app_service_version = get_response('web_app_service_version.json', True)
    mock_obj = [vm_instance, vm_instance_os_pkgs, vm_instance_os_vuln,
                web_app, web_app_service, web_app_service_version]
    return mock_obj


def mock_history_response():
    # Mock get_asset_history responses
    vm_instance = get_response('vm_instance_history.json', True)
    vm_instance_os_pkgs = get_response('vm_instance_os_pkgs_history.json', True)
    vm_instance_os_vuln = get_response('vm_instance_os_vuln_history.json', True)
    vm_instance_update = get_response('vm_instance_update_history.json', True)
    vm_instance_os_pkgs_updated = get_response('vm_instance_os_pkgs_history.json', True)
    vm_instance_os_vuln_updated = get_response('vm_instance_os_vuln_history.json', True)
    web_app = get_response('web_app.json', True)
    web_app_service = get_response('web_app_service.json', True)
    web_app_service_version = get_response('web_app_service_version.json', True)
    mock_obj = [vm_instance, vm_instance_os_pkgs, vm_instance_os_vuln,
                vm_instance_update, vm_instance_os_pkgs_updated, vm_instance_os_vuln_updated,
                web_app, web_app_service, web_app_service_version]
    return mock_obj
