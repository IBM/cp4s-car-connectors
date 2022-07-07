import unittest
from unittest.mock import patch
from tests.test_utils import full_import_initialization,\
              create_vertices_edges, validate_all_handler, mocking_apis


class TestInitialImportFunctions(unittest.TestCase):

    """Unit test for full import"""
    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_collection(self, mock_asset):
        """unit test for import collection"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # Mock API's
        mock_asset.side_effect = mocking_apis()

        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_collection_without_application(self, mock_asset):
        """unit test for import collection without application data"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # Mock API's
        mocking_api = mocking_apis()
        mocking_api[2] = {"deployments": []}
        mock_asset.side_effect = mocking_api

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
