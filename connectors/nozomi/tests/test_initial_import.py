import unittest
from unittest.mock import patch
import json
from tests.test_utils import full_import_initialization, \
    create_vertices_edges, validate_all_handler, get_response, NozomiMockResponse


class TestInitialImportFunctions(unittest.TestCase):
    """Unit test for full import"""

    @patch('car_framework.car_service.CarService.get_import_schema')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_collection(self, mock_results, mock_schema):
        """unit test for import collection"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock data source API responses
        login_response = json.dumps(get_response('login_response.json', True))
        query_assets = json.dumps(get_response('query_assets.json', True))
        query_sensors = json.dumps(get_response('query_sensors.json', True))
        query_nodes = json.dumps(get_response('query_nodes.json', True))
        query_software_list = json.dumps(get_response('query_softwares_list.json', True))
        query_asset_softwares = json.dumps(get_response('query_asset_softwares.json', True))
        query_vulnerabilities = json.dumps(get_response('query_vulnerabilities.json', True))
        mock_schema.return_value = get_response('schema.json', True)
        mock_results.side_effect = [NozomiMockResponse(200, login_response, headers={'Authorization': 'bearer xxxxxx'}),
                                    NozomiMockResponse(200, query_assets),
                                    NozomiMockResponse(200, query_sensors),
                                    NozomiMockResponse(200, query_nodes),
                                    NozomiMockResponse(200, query_software_list),
                                    NozomiMockResponse(200, query_asset_softwares),
                                    NozomiMockResponse(200, query_vulnerabilities)]
        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    def test_get_new_model_state_id(self):
        """unitest for model_state_id"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        date_id = full_import_obj.get_new_model_state_id()
        assert date_id is not None
