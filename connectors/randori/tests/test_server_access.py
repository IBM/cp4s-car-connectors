import unittest
from unittest.mock import patch
from car_framework.context import context
from tests.test_utils import full_import_initialization, get_response, RandoriMockResponse

class TestAssetServer(unittest.TestCase):
    """Unit test for server access functions"""

    @patch('randori_api.api.default_api.DefaultApi.get_hostname')
    def test_connection(self, mock_res):
        """Unit test for test_connection"""

        mock_api_return_value = get_response('hostnames.json', True)
        mock_hostnames_res = RandoriMockResponse(200, mock_api_return_value)
        mock_res.return_value = mock_hostnames_res

        actual_response = context().asset_server.test_connection()
        assert actual_response is 0

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

