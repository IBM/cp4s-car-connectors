import unittest
import datetime
from unittest.mock import patch
from car_framework.context import Context, context
from connector import server_access, inc_import, data_handler
from connector.data_handler import endpoint_mapping
from tests.convert_from_json import JsonResponse
from tests import data_handler_validator
from tests.test_utils import create_vertices_edges, Arguments


def import_initialization():
    """incremental import initialization"""
    Context(Arguments)
    context().asset_server = server_access.AssetServer()
    inc_import_obj = inc_import.IncrementalImport()
    return inc_import_obj


class TestIncImportFunctions(unittest.TestCase):
    """unittest for incremental run"""

    @patch('connector.server_access.AssetServer.get_collection')
    @patch('connector.inc_import.IncrementalImport.get_active_vulnerability')
    def test_incremental_update(self, mock_api_res, mock_active_vul):

        """Unit test for import collection"""

        inc_import_obj = import_initialization()
        inc_import_obj.create_source_report_object()
        mock_active_vul.return_value = ['ecb8e938619ad370e070ff7e8426b89cb57f1861b736ac5991fa46c34b902f35']
        inc_import_obj.delta = JsonResponse(200, 'tests_delta.json').json()
        inc_import_obj.last_model_state_id = data_handler.get_report_time()

        for key in endpoint_mapping:
            if key == 'siem':
                mock_api_res.return_value = JsonResponse(
                    200, 'siem_api.json').json()
            else:
                mock_api_res.return_value = JsonResponse(
                    200, 'people_api.json').json()
            inc_import_obj.import_collection(key, endpoint_mapping.get(key))
        actual_resp = inc_import_obj.data_handler.collections
        data_handler_obj = data_handler_validator.TestConsumer()
        validation = all([data_handler_obj.handle_assets(
            actual_resp['asset']),
            data_handler_obj.handle_vulnerabilities(
               actual_resp['vulnerability']),
            data_handler_obj.handle_accounts(
                actual_resp['account']),
            data_handler_obj.handle_users(
                actual_resp['user'])])
        assert validation is True
        assert actual_resp is not None

    @patch('connector.server_access.AssetServer.get_collection')
    @patch('connector.inc_import.IncrementalImport.get_active_vulnerability')
    def test_incremental_create(self, mock_api_res, mock_active_vul):

        """Unit test for import collection"""

        inc_import_obj = import_initialization()
        inc_import_obj.create_source_report_object()
        mock_active_vul.return_value = ['']
        inc_import_obj.delta = JsonResponse(200, 'tests_delta.json').json()
        inc_import_obj.last_model_state_id = data_handler.get_report_time()

        for key in endpoint_mapping:
            if key == 'siem':
                mock_api_res.return_value = JsonResponse(
                    200, 'siem_api.json').json()
            else:
                mock_api_res.return_value = JsonResponse(
                    200, 'people_api.json').json()
            inc_import_obj.import_collection(key, endpoint_mapping.get(key))
        response = inc_import_obj.data_handler.collections
        data_handler_obj = data_handler_validator.TestConsumer()
        validate = all([data_handler_obj.handle_assets(
            response['asset']),
            data_handler_obj.handle_vulnerabilities(
                response['vulnerability']),
            data_handler_obj.handle_accounts(
                response['account']),
            data_handler_obj.handle_users(
                response['user'])])
        assert validate is True
        assert response is not None

    @patch('connector.inc_import.IncrementalImport.get_active_vulnerability')
    def test_import_vertices(self, mock_active_vul):

        """Unit test for import vertices"""

        inc_import_obj = import_initialization()
        inc_import_obj.initial_import_interval_days = 0
        inc_import_obj.create_source_report_object()
        mock_active_vul.return_value = ['ecb8e938619ad370e070ff7e8426b89cb57f1861b736ac5991fa46c34b902f35']
        inc_import_obj.delta = JsonResponse(200, 'tests_delta.json').json()
        inc_import_obj.last_model_state_id = data_handler.get_report_time()
        validations, actual_response = create_vertices_edges(inc_import_obj)
        assert validations is True
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.delete')
    @patch('connector.server_access.AssetServer.get_collection')
    @patch('connector.inc_import.IncrementalImport.get_active_vulnerability')
    def test_delete_vertices(self, mock_active_vul, mock_api_res, mock_del_res):
        """unittest for delete vertices"""

        mock_active_vul.return_value = ['2d8367310dc9a70341f04d39f18261641eb403c019bedbf288203d17647053cf']
        inc_import_obj = import_initialization()
        inc_import_obj.create_source_report_object()
        mock_api_res.return_value = JsonResponse(200, 'threat_summary.json').json()
        mock_del_res.return_value = {'status': 'success'}
        inc_import_obj.delete_vertices()
        assert 'status' in mock_del_res.return_value

    @patch('connector.server_access.AssetServer.get_model_state_delta')
    @patch('car_framework.car_service.CarService.graph_attribute_search')
    def test_data_delta(self, mock_delta, mock_active_vul):
        """unittest for get last run"""
        inc_import_obj = import_initialization()
        inc_import_obj.create_source_report_object()
        mock_delta.return_value = JsonResponse(200, 'tests_delta.json').json()
        mock_active_vul.return_value = JsonResponse(200, 'active_vulnerability.json').json()
        last_model_state_id = datetime.datetime(2019, 10, 6, 13, 25, 35)
        new_model_state_id = datetime.datetime(2019, 11, 6, 13, 25, 35)
        inc_import_obj.get_data_for_delta(last_model_state_id,
                                           new_model_state_id)
        assert isinstance(
            inc_import_obj.last_model_state_id,
            datetime.datetime)

    @patch('car_framework.car_service.CarService.graph_attribute_search')
    def test_get_new_model_state_id(self, mock_active_vul):
        """unitest for model_state_id"""
        inc_import_obj = import_initialization()
        inc_import_obj.create_source_report_object()
        mock_active_vul.return_value = JsonResponse(200, 'active_vulnerability.json').json()
        date_id = inc_import_obj.get_new_model_state_id()
        assert date_id is not None
