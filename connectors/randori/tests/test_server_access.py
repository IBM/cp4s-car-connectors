import unittest
from unittest.mock import patch
from car_framework.context import context
from tests.test_utils import full_import_initialization, get_response, RandoriMockResponse

class TestAssetServer(unittest.TestCase):
    """Unit test for server access functions"""

    def test_get_collection_error(self):
        """unit test for get_collection"""
        try:
            full_import_obj = full_import_initialization()
            full_import_obj.create_source_report_object()
            error_response = None
            context().asset_server.get_collection('')
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('connector.server_access.AssetServer.get_object')
    def test_get_object(self, mock_object):
        """unit test for test object"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_api_return_value = get_response('hostname.json', True)
        mock_hostname_res = RandoriMockResponse(200, mock_api_return_value)
        mock_object.return_value = mock_hostname_res

        # Initiate get_users function
        actual_response = context().asset_server.get_object('recon/api/v1/hostname', '0237c69b-4faf-41d7')

        assert actual_response is not None
        assert '0237c69b-4faf-41d7' in actual_response.json()

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_assets(self, mock_collections):
        """Unit test for get_collection"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_api_return_value = get_response('hostnames.json', True)
        mock_hostnames_res = RandoriMockResponse(200, mock_api_return_value)
        mock_collections.return_value = mock_hostnames_res

        actual_response = context().asset_server.get_collection('recon/api/v1/hostname')
        assert actual_response is not None
        assert '08cbbbaa-d609' == actual_response.json()[1]['id']

    @patch('connector.server_access.AssetServer.get_detections_for_target')
    def test_get_detections_for_target(self, mock_detections_for_target):
        """Unit test for get_collection"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_api_return_value = get_response('detections_for_target.json', True)
        mock_hostnames_res = RandoriMockResponse(200, mock_api_return_value)
        mock_detections_for_target.return_value = mock_hostnames_res

        actual_response = context().asset_server.get_detections_for_target()
        assert actual_response is not None

