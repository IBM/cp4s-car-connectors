import os
import json
from unittest.mock import patch, Mock
from tests import data_handler_validator
from car_framework.context import Context, context
from connector import full_import, server_access, inc_import


class Arguments:
    """Test args for Unit test case"""
    host = "test.com"
    port = ""
    gateway = ""
    username = ""
    token = ""
    source = "RHACS"
    car_service_apikey_url = "https://app.demo.isc.ibm"
    api_key = "abcdef"
    api_password = ""
    car_service_token_url = None
    api_token = None
    store_true = False
    export_data_dir = "tests/tmp/car_temp_export_data"
    keep_export_data_dir = "store_true"
    export_data_page_size = 2000
    description = "description"
    debug = None
    connector_name = "rhacs"
    version = '1.0'


class RHACSMockResponse:
    """class for rhacs mock api response"""

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

    validations = all([data_handler_obj.handle_cluster(actual_response['asset']),
                       data_handler_obj.handle_node(actual_response['asset']),
                       data_handler_obj.handle_container(actual_response['asset']),
                       data_handler_obj.handle_application(actual_response['application']),
                       data_handler_obj.handle_account(actual_response['account']),
                       data_handler_obj.handle_user(actual_response['user']),
                       data_handler_obj.handle_vulnerability(actual_response['vulnerability']),
                       data_handler_obj.handle_ipaddress(actual_response['ipaddress'])])
    return validations


def mocking_apis():
    """mock api as per sequence"""
    mock_cluster_obj = get_response('clusters.json', True)
    mock_nodes_obj = get_response('nodes.json', True)
    mock_deployements_obj = get_response('deployments.json', True)
    mock_pods_obj = get_response('pods.json', True)
    mock_image_obj = get_response('image.json', True)
    mock_image_obj_json = RHACSMockResponse(200, mock_image_obj)
    mock_roles_obj = get_response('roles.json', True)
    mock_groups_obj = get_response('groups.json', True)
    mock_users_obj = get_response('users.json', True)

    mock_obj = [mock_cluster_obj, mock_nodes_obj, mock_deployements_obj,
                mock_pods_obj, mock_image_obj_json, mock_roles_obj,
                mock_groups_obj, mock_users_obj]
    return mock_obj
