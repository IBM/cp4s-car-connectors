import unittest
from unittest.mock import patch
from tests.test_utils import full_import_initialization, create_vertices_edges
from tests import data_handler_validator
from tests.convert_from_json import JsonResponse
from connector.data_handler import endpoint_mapping
from connector import data_handler


class TestInitialImportFunctions(unittest.TestCase):

    """Unit test for full import"""

    def test_full_import_initialization(self):

        """Unit test for Full_Import Initialization"""

        full_import_obj = full_import_initialization()
        assert full_import_obj.config['parameter'].get("format") == 'json'
        assert full_import_obj.config['parameter'].get("interval_days") == 7

    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_vertices(self, mock_api):

        """Unit test for import vertices"""
        full_import_obj = full_import_initialization()
        full_import_obj.config['parameter']['interval_days'] = 0.01
        full_import_obj.create_source_report_object()
        mock_siem_api = JsonResponse(200, 'siem_api.json').json()
        mock_people_api = JsonResponse(200, 'people_api.json').json()
        mock_api.side_effect = [mock_siem_api, mock_people_api]
        validations, actual_response = create_vertices_edges(full_import_obj)
        assert validations is True
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_collection(self, mock_api_res):

        """Unit test for import collection"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        for key in data_handler.endpoint_mapping:
            if key == 'siem':
                mock_api_res.return_value = JsonResponse(
                                              200, 'siem_api.json').json()
            else:
                mock_api_res.return_value = JsonResponse(
                                              200, 'people_api.json').json()
            full_import_obj.import_collection(key, endpoint_mapping[key])
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
        assert validations is True
        assert actual_response is not None

    def test_get_new_model_state_id(self):
        """unitest for model_state_id"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        date_id = full_import_obj.get_new_model_state_id()
        assert date_id is not None

    def test_get_report_time(self):
        """
        Convert current utc time to epoch time
        """
        milli_sec = data_handler.get_report_time()
        assert isinstance(milli_sec, float)
