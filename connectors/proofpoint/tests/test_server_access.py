from datetime import datetime
import unittest
from unittest.mock import patch, Mock
from car_framework.context import context
from tests.test_utils import full_import_initialization
from tests.convert_from_json import JsonResponse
from connector import full_import, server_access, data_handler


class TestAssetServer(unittest.TestCase):
    """Unit test for API"""

    @patch('connector.server_access.requests')
    def test_get_collection(self, mock_requests):
        """Unit test for proofpoint api"""

        # Mocking the requests.get response
        mock_requests.get.return_value = JsonResponse(
            200, 'siem_api_click_msg.json')
        full_import_initialization()
        full_import.FullImport()
        response = server_access.AssetServer.get_collection(
                context().asset_server, 'v2')
        assert response is not None

    @patch('connector.server_access.requests')
    def test_get_collection_with_exception(self, mock_requests):
        """Unit test for proofpoint api,
        raises exception when time range is beyond 7 days"""

        # Mocking the requests.get res
        api_response = Mock()
        api_response.status_code = 400
        api_response.content = b'The requested start time is too far into the past.' \
                               b'Requests for information up to 7.00d are accepted'
        api_response.text = "The requested start time is too far into the past"
        api_response.json.return_value = []
        mock_requests.get.return_value = api_response
        full_import_initialization()
        full_import.FullImport()
        error_response = None
        try:
            server_access.AssetServer.get_collection(
                context().asset_server, 'v2')
        except Exception as e:
            error_response = str(e)

        assert error_response is not None

    @patch('connector.server_access.requests')
    def test_get_collection_with_error(self, mock_requests):
        """Unit test for proofpoint api call failures"""

        # Mocking the requests.get res
        api_response = Mock()
        api_response.status_code = 404
        api_response.text = ''
        api_response.content = b'{"message":"HTTP 404 Not Found"}\n'
        api_response.json.return_value = []
        mock_requests.get.return_value = api_response
        full_import_initialization()
        full_import.FullImport()
        with self.assertRaises(SystemExit) as ex:
            server_access.AssetServer.get_collection(
                context().asset_server, 'v2')
        self.assertEqual(ex.exception.code, 50)

    @patch('connector.server_access.AssetServer.get_collection')
    @patch('connector.server_access.AssetServer.get_siem_api')
    def test_state_delta(self, mock_api_res, mock_peop_res):
        """unittest for get_latest_id"""
        full_import_initialization()
        last_model_state_id = datetime(2019, 10, 6, 13, 25, 35)
        new_model_state_id = datetime(2019, 11, 6, 13, 25, 35)
        context().asset_server.get_model_state_delta(last_model_state_id, new_model_state_id)
        mock_api_res.return_value = JsonResponse(
            200, 'siem_api_click_msg.json').json()
        mock_peop_res.return_value = JsonResponse(
            200, 'people_api.json').json()

    @patch('connector.server_access.AssetServer.get_collection')
    def test_siem_api(self, mock_api_res):
        """unittest for get_siem_api"""
        start_time = data_handler.get_report_time() - 3600
        full_import_initialization()
        context().asset_server.get_siem_api(start_time)
        mock_api_res.return_value = JsonResponse(
            200, 'siem_api.json').json()
