import unittest
from unittest.mock import patch
from car_framework.context import context
from tests.test_utils import full_import_initialization, get_response, RHACSMockResponse


class TestAssetServer(unittest.TestCase):
    """Unit test for server access functions"""

    def test_get_collection_error(self):
        """unit test for get_collection"""
        try:
            error_response = None
            full_import_obj = full_import_initialization()
            full_import_obj.create_source_report_object()
            context().asset_server.get_collection('')
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_connection(self, mock_connection):
        """unit test for test connection"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_connection.return_value = RHACSMockResponse(200, [])

        # Initiate get_assets function
        actual_response = context().asset_server.test_connection()

        assert actual_response == 0

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_assets(self, mock_asset):
        """Unit test for get_assets"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_cluster_obj = get_response('clusters.json', True)

        mock_node_obj = get_response('nodes.json', True)

        mock_asset.side_effect = [mock_cluster_obj, mock_node_obj]

        # Initiate get_assets function
        actual_response = context().asset_server.get_assets()
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_assets_error(self, mock_asset):
        """Unit test for get_assets. cluster and node have empty lists"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_response = {'clusters': [], 'nodes': []}
        mock_asset.side_effect = [mock_response]

        # Initiate get_assets function
        cluster, node = context().asset_server.get_assets()

        assert cluster == []
        assert node == []
