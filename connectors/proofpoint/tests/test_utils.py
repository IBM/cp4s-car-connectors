from unittest.mock import patch
from car_framework.context import Context, context
from connector import full_import, server_access
from tests import data_handler_validator


class Arguments:
    """Test args for Unit test case"""
    server = "https://tap-api-v2.proofpoint.com/"
    username = ""
    password = ""
    source = "Proofpoint"
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
    connector_name = "test-connector-name"
    version = "0.0.0",


class ImportDataReturnObj:
    status = 1
    status_code = 200
    error = 'Inknown'
    job_id = '30a0f27d-cf5e-45ca-9e35-4b2add18a0c7-72a7a4eb-a433-49c6-b110-51569d55c915-asset'


def full_import_initialization():
    """
    create full import object
    """
    Context(Arguments)
    context().asset_server = server_access.AssetServer()
    full_import_obj = full_import.FullImport()
    return full_import_obj


@patch('car_framework.car_service.CarService.import_data_from_file')
def create_vertices_edges(full_import_obj, mock_import):
    """tests for vertices and edges"""

    mock_import.return_value = ImportDataReturnObj
    full_import_obj.import_vertices()
    full_import_obj.import_edges()
    actual_response = full_import_obj.data_handler.collections
    data_handler_obj = data_handler_validator.TestConsumer()
    validations = all([data_handler_obj.handle_assets(
        actual_response['asset']),
        data_handler_obj.handle_vulnerabilities(
            actual_response['vulnerability']),
        data_handler_obj.handle_accounts(
            actual_response['account']),
        data_handler_obj.handle_users(
            actual_response['user'])])
    return validations, actual_response
