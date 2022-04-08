import unittest
from connector import data_handler
from unittest.mock import patch
from tests.test_utils import full_import_initialization,\
              create_vertices_edges, get_response,\
              validate_all_handler, CybereasonMockResponse


class TestInitialImportFunctions(unittest.TestCase):

    """Unit test for full import"""

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_asset_vuln_records(self, mock_api):
        """Unit test for get_asset_vuln_records"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_asset_res = get_response('assets_api.json', True)
        mock_netwrk_res = get_response('network_interface.json', True)
        mock_vuln_res = get_response('vulnerability_api.json', True)

        mock_asset = CybereasonMockResponse(200,mock_asset_res)
        mock_netwrk = CybereasonMockResponse(200,mock_netwrk_res)
        mock_vuln = CybereasonMockResponse(200,mock_vuln_res)

        mock_api.side_effect = [mock_asset,mock_netwrk,mock_vuln]

        collection_res = full_import_obj.get_asset_vuln_records()
        assert isinstance(collection_res, dict)

    @patch('connector.full_import.FullImport.get_asset_vuln_records')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_collection(self, mock_auth, mock_asset):
        """unit test for import collection"""

        mock_auth.return_value = {'status_code':200}
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_asset.return_value = get_response('asset_collection.json', True)
        full_import_obj.import_collection()

        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('connector.full_import.FullImport.get_asset_vuln_records')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_vertices(self, mock_auth, mock_asset):
        """Unit test for import_vertices"""

        mock_auth.return_value = {'status_code': 200}
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_asset.return_value = get_response('asset_collection.json', True)
        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_new_model_state_id(self, mock_auth):
        """unitest for model_state_id"""

        mock_auth.return_value = {'status_code': 200}
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        date_id = full_import_obj.get_new_model_state_id()

        assert date_id is not None

    def test_get_report_time(self):
        """Convert current ut time to epoch time"""

        milli_sec = data_handler.get_report_time()
        assert isinstance(milli_sec, float)
