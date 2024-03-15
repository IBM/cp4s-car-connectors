import json
import unittest
from unittest.mock import patch

from tests.test_utils import inc_import_initialization, create_vertices_edges, \
    validate_all_handler, get_response, NozomiMockResponse


class TestIncrementalImportFunctions(unittest.TestCase):
    """Unit test for incremental import"""

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('car_framework.car_service.CarService.get_import_schema')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create_update(self, mock_results, mock_schema, mock_collections):
        """unit test for incremental create and update"""
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        inc_import_obj.get_data_for_delta(1781375759000, None)
        # mock query responses for asset, node, application, vulnerability
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
        collections = get_response('car_search_collection.json', True)
        mock_collections.side_effect = [collections['asset_ipaddress'], collections['asset_macaddress'],
                                        collections['asset_application'], collections['asset_geolocation']]
        actual_response = create_vertices_edges(inc_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.delete')
    @patch('car_framework.car_service.CarService.query_graphql')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_increment_delete(self, mock_results, mock_search, mock_delete):
        """unit test for incremental delete"""
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        inc_import_obj.update_edge = []
        inc_import_obj.get_data_for_delta(1662009569000, None)
        login_response = json.dumps(get_response('login_response.json', True))
        query_vulnerabilities = json.dumps(get_response('query_vulnerabilities.json', True))
        search_res = get_response('car_graphql_search.json', True)
        mock_results.side_effect = [NozomiMockResponse(200, login_response, headers={'Authorization': 'bearer xxxxxx'}),
                                    NozomiMockResponse(200, query_vulnerabilities)]
        mock_search.side_effect = [search_res['asset'], search_res['asset_ipaddress'], search_res['asset_macaddress'],
                                   search_res['asset_application'], search_res['asset_vulnerability']]
        # Mock Edge patch response
        mock_delete.return_value = {'status': 'success'}
        assert inc_import_obj.delete_vertices() is None