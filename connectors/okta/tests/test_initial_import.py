import unittest
from connector import data_handler
from unittest.mock import patch
from tests.test_utils import full_import_initialization,\
              create_vertices_edges, get_response,\
              validate_all_handler


class TestInitialImportFunctions(unittest.TestCase):
    """Unit test for full import"""

    @patch('connector.server_access.AssetServer.get_asset_collections')
    def test_import_collection(self, mock_asset):
        """unit test for import collection"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_asset.return_value = get_response('asset_collection.json', True)
        full_import_obj.import_collection()

        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_asset_collections')
    def test_import_vertices(self, mock_asset):
        """Unit test for import_vertices"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_asset.return_value = get_response('asset_collection.json', True)
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

    def test_get_report_time(self):
        """Convert current ut time to epoch time"""
        milli_sec = data_handler.get_report_time()
        assert isinstance(milli_sec, float)
