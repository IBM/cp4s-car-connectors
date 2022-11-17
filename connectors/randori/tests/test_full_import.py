import unittest
from unittest.mock import patch
from tests.test_utils import full_import_initialization, \
    get_response, RandoriMockResponse, create_vertices_edges, validate_all_handler
from datetime import datetime


class TestImportFull(unittest.TestCase):
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

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        full_import_obj.import_collection()

        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None


