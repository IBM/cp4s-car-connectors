
import unittest
from unittest.mock import patch
from car_framework.context import context
from tests.test_utils import full_import_initialization, get_response, TaniumMockResponse

class TestAssetServer(unittest.TestCase):
    """Unit test for server access functions"""

    @patch('connector.server_access.AssetServer.execute_query')
    def test_connection(self, mock_res):
        """Unit test for test_connection"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_api_return_value = get_response('test_connection_resp.json', True)
        mock_test_res = TaniumMockResponse(200, mock_api_return_value)
        mock_res.return_value = mock_test_res

        actual_response = context().asset_server.test_connection()
        assert actual_response is 0

    @patch('connector.server_access.AssetServer.execute_query')
    def test_query_tanium_endpoints(self, mock_query_tanium_endpoints):
        """Unit test for get_collection"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_api_return_value = get_response('tanium_node_resp.json', True)
        mock_hostnames_res = TaniumMockResponse(200, mock_api_return_value)
        mock_query_tanium_endpoints.return_value = mock_hostnames_res

        actual_response = context().asset_server.query_tanium_endpoints()
        assert actual_response is not None
        assert actual_response['data']['endpoints']['edges'] is not None
        assert actual_response['data']['endpoints']['edges'][0]['node']['ipAddress'] == '172.31.76.205'

