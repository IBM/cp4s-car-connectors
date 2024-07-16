import json
import unittest
from unittest.mock import patch
from connector import server_access
from car_framework.context import context
from tests.test_utils import NozomiMockResponse, full_import_initialization, get_response


class TestAssetServer(unittest.TestCase):
    """Unit test for server access functions"""

    def test_get_collection(self):
        """unit test for get_collection"""
        try:
            server_access.AssetServer.get_collection('POST', context().asset_server, None)
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_connection(self, mock_collection):
        """unit test for test connection"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        login_response = json.dumps(get_response('login_response.json', True))
        mock_collection.return_value = NozomiMockResponse(200, login_response)
        actual_response = context().asset_server.test_connection()
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_connection_with_error(self, mock_collection):
        """unit test for test connection failure"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        error_response = json.dumps(get_response('api_auth_error.json', True))
        mock_collection.return_value = NozomiMockResponse(401, error_response)
        actual_response = context().asset_server.test_connection()
        assert actual_response == 1

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_bearer_token(self, mock_collection):
        """unit test for bearer token"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        login_response = json.dumps(get_response('login_response.json', True))
        mock_collection.return_value = NozomiMockResponse(200, login_response,
                                                          headers={'Authorization': 'bearer xxxxxx'})
        token = context().asset_server.get_bearer_token()
        assert token is not None
        assert token == 'bearer xxxxxx'

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_bearer_token_invalid_url(self, mock_collection):
        """unit test for bearer token with invalid endpoint"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        login_response = ''
        mock_collection.return_value = NozomiMockResponse(404, login_response, url="https://nozomi/log-in1")
        try:
            context().asset_server.get_bearer_token()
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_bearer_token_with_error(self, mock_collection):
        """unit test for bearer token with authentication failure"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        error_response = json.dumps(get_response('api_auth_error.json', True))
        mock_collection.return_value = NozomiMockResponse(401, error_response)
        try:
            context().asset_server.get_bearer_token()
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_query_results(self, mock_collection):
        """unit test for get_query_results"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        login_response = json.dumps(get_response('login_response.json', True))
        query_response = json.dumps(get_response('query_assets.json', True))
        mock_collection.side_effect = [NozomiMockResponse(200, login_response,
                                                          headers={'Authorization': 'bearer xxxxxx'}),
                                       NozomiMockResponse(200, query_response)]

        asset_list = context().asset_server.get_query_results(category='asset')
        assert asset_list is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_query_results_invalid_url(self, mock_collection):
        """unit test for get_query_results with invalid endpoint"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        login_response = json.dumps(get_response('login_response.json', True))
        query_response = ''
        mock_collection.side_effect = [NozomiMockResponse(200, login_response,
                                                          headers={'Authorization': 'bearer xxxxxx'}),
                                       NozomiMockResponse(404, query_response)]
        try:
            context().asset_server.get_query_results(category='asset')
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_query_results_expired_token(self, mock_collection):
        """unit test for get_query_results with expired token"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        context().asset_server.headers['Authorization'] = 'bearer xxxxxx'
        login_response = json.dumps(get_response('login_response.json', True))
        query_response = json.dumps(get_response('query_assets.json', True))
        mock_collection.side_effect = [NozomiMockResponse(401, ''),
                                       NozomiMockResponse(200, login_response,
                                                          headers={'Authorization': 'bearer xxxxxx'}),
                                       NozomiMockResponse(200, query_response)]
        asset_list = context().asset_server.get_query_results(category='asset')
        assert asset_list is not None