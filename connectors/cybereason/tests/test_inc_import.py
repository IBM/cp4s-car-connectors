import unittest
import json
from connector import data_handler
from unittest.mock import patch
from tests.test_utils import inc_import_initialization, create_vertices_edges, \
    get_response, validate_all_handler, CybereasonMockResponse


class TestIncrementalImportFunctions(unittest.TestCase):
    """Unit test for full import"""

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create(self, mock_api, active_edges):
        """Test Incremental create"""
        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        # mock asset, network, vulnerability api
        inc_create_collections = get_response('inc_create_collections.json', True)

        mock_asset_res = json.dumps(inc_create_collections["asset"])
        mock_netwrk_res = json.dumps(inc_create_collections["network_interface"])
        mock_vuln_res = json.dumps(inc_create_collections["vulnerability"])

        mock_asset = CybereasonMockResponse(200, mock_asset_res)
        mock_netwrk = CybereasonMockResponse(200, mock_netwrk_res)
        mock_vuln = CybereasonMockResponse(200, mock_vuln_res)

        mock_api.side_effect = [mock_asset, mock_netwrk, mock_vuln]
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)

        # Mock active edge response
        active_edges.return_value = []
        # Initiate incremental create and update
        actual_response = create_vertices_edges(inc_import_obj)

        # validate the response
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('car_framework.car_service.CarService.search_collection')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_update(self, mock_api, active_edges, active_nodes):
        """Test Incremental create"""

        # Initialization
        # Mock active edge response
        active_car_edges = get_response('active_car_edges.json', True)
        active_edges.side_effect = [active_car_edges["asset_ipaddress"], active_car_edges["ipaddress_macaddress"],
                                    active_car_edges["asset_hostname"], active_car_edges["asset_vulnerability"]]

        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        # mock asset, network, vulnerability api
        inc_create_collections = get_response('inc_update_collections.json', True)

        mock_asset_res = json.dumps(inc_create_collections["asset"])
        mock_netwrk_res = json.dumps(inc_create_collections["network_interface"])
        mock_vuln_res = json.dumps(inc_create_collections["vulnerability"])

        mock_asset = CybereasonMockResponse(200, mock_asset_res)
        mock_netwrk = CybereasonMockResponse(200, mock_netwrk_res)
        mock_vuln = CybereasonMockResponse(200, mock_vuln_res)

        # malop remediation status
        remediation_status = get_response('malop_remediation_status.json')
        mock_remediation_res = CybereasonMockResponse(200, remediation_status)

        mock_api.side_effect = [mock_asset, mock_netwrk, mock_vuln, mock_remediation_res]
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)

        # Active assets in CAR DB
        active_nodes.return_value = get_response('active_car_asset.json', True)
        # Initiate incremental create and update
        actual_response = create_vertices_edges(inc_import_obj)

        # validate the response
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('car_framework.car_service.CarService.delete')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_delete(self, mock_api, mock_car_delete, active_edges):
        """Test Incremental create"""
        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        mock_car_delete.return_value = {'status': 'success'}

        # mock asset, network, vulnerability api
        inc_delete_collections = get_response('inc_delete_collections.json', True)

        mock_asset_res = json.dumps(inc_delete_collections["asset"])
        mock_netwrk_res = json.dumps(inc_delete_collections["network_interface"])
        mock_vuln_res = json.dumps(inc_delete_collections["vulnerability"])

        mock_asset = CybereasonMockResponse(200, mock_asset_res)
        mock_netwrk = CybereasonMockResponse(200, mock_netwrk_res)
        mock_vuln = CybereasonMockResponse(200, mock_vuln_res)

        mock_api.side_effect = [mock_asset, mock_netwrk, mock_vuln]
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)
        # Mock active edge response
        active_edges.return_value = []
        inc_import_obj.delete_vertices()

        assert len(inc_import_obj.delete_vulnerability) != 0

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_new_model_state_id(self, mock_auth, active_edges):
        """unitest for model_state_id"""

        mock_auth.return_value = {'status_code': 200}
        full_import_obj = inc_import_initialization()
        full_import_obj.create_source_report_object()
        # Mock active edge response
        active_edges.return_value = []
        date_id = full_import_obj.get_new_model_state_id()
        assert date_id is not None
