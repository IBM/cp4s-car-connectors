import json
import unittest
from unittest.mock import patch
from tests.test_utils import full_import_initialization, \
    get_response, RandoriMockResponse, create_vertices_edges, validate_all_handler
from datetime import datetime
from connector.data_handler import endpoint_mapping
from unittest.mock import patch, PropertyMock


def get_mock_data_from_file(asset_server_endpoint):
    with open(f'tests/mock_data/{asset_server_endpoint}.json', 'r') as f:
        return json.load(f)

class TestImportFull(unittest.TestCase):
    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_collection(self, mock_get_collection):
        """
             unit test for importing collections.
        """
        mock_get_collection.side_effect = get_mock_data_from_file

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None


