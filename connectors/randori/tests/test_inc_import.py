import unittest
from connector import data_handler
from unittest.mock import patch
from tests.test_utils import inc_import_initialization, \
    get_response, RandoriMockResponse, create_vertices_edges, validate_all_handler
from datetime import datetime


class TestIncImportFunctions(unittest.TestCase):
    @patch('connector.server_access.AssetServer.get_detections_for_target')
    def test_import_collection(self, mock_detections_list):
        """
             unit test for importing collections.
        """
        mock_response = get_response('detections_for_target_full_import.json', True)
        mock_data_list = []
        for data in mock_response['data']:
            data['first_seen'] = datetime.fromisoformat(data['first_seen'])
            data['last_seen'] = datetime.fromisoformat(data['last_seen'])
            mock_data_list.append(data)

        mock_detections_list.return_value.data = mock_data_list

        inc_import_obj = inc_import_initialization()
        inc_import_obj.last_model_state_id = data_handler.get_report_time()
        inc_import_obj.create_source_report_object()
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)
        inc_import_obj.import_collection()

        actual_response = create_vertices_edges(inc_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None


