import pytest
from unittest.mock import Mock, patch
import requests
import unittest
from connector import server_access
class TestAssetServer(unittest.TestCase):
    @patch('connector.server_access.context')
    def test_get_object(self, mock_context):
        mock_context.return_value.args.CONNECTION_HOST = 'http://localhost'
        asset_server = server_access.AssetServer()
        asset_server.get_collection = Mock()
        asset_server.get_collection.return_value = [
            {'pk': 1, 'name': 'Asset1'},
            {'pk': 2, 'name': 'Asset2'},
            {'pk': 3, 'name': 'Asset3'}
        ]
        url = 'http://localhost/assets/2'

        result = asset_server.get_object(url)

        assert result == {'pk': 2, 'name': 'Asset2'}
        
    @patch('connector.server_access.context')
    def test_get_objects(self, mock_context):
        mock_context.return_value.args.CONNECTION_HOST = 'http://localhost'
        asset_server = server_access.AssetServer()
        asset_server.get_collection = Mock()
        asset_server.get_collection.return_value = [
            {'pk': 1, 'name': 'Asset1'},
            {'pk': 2, 'name': 'Asset2'},
            {'pk': 3, 'name': 'Asset3'}
        ]
        asset_server_endpoint = 'http://localhost/assets'
        ids = [1, 3]

        result = asset_server.get_objects(asset_server_endpoint, ids)

        assert result == [{'pk': 1, 'name': 'Asset1'}, {'pk': 3, 'name': 'Asset3'}]
        asset_server.get_collection.assert_called_once_with(asset_server_endpoint)

    @patch('connector.server_access.context')
    @patch.object(requests, 'get')
    def test_get_collection(self, mock_get, mock_context):
        mock_context.return_value.args.CONNECTION_HOST = 'http://localhost'
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {'pk': 1, 'name': 'Asset1'},
            {'pk': 2, 'name': 'Asset2'},
            {'pk': 3, 'name': 'Asset3'}
        ]
        asset_server = server_access.AssetServer()
        asset_server_endpoint = 'assets'

        result = asset_server.get_collection(asset_server_endpoint)

        assert result == [{'pk': 1, 'name': 'Asset1'}, {'pk': 2, 'name': 'Asset2'}, {'pk': 3, 'name': 'Asset3'}]
        mock_get.assert_called_once_with('http://localhost/assets.json')