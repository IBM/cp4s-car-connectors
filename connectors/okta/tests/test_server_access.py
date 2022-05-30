import unittest
from unittest.mock import patch
from car_framework.context import context
from connector import server_access
from tests.test_utils import full_import_initialization, get_response,\
                             OktaMockResponse


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
    def test_get_assets(self, mock_asset):
        """Unit test for get_assets. If host asset api having pagination"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset
        mock_api_return_value = get_response('assets_mock_res.json', True)
        mock_asset_res = OktaMockResponse(200, mock_api_return_value)
        mock_asset_res.links = {}
        mock_asset.return_value = mock_asset_res

        # Initiate get_assets function
        actual_response = context().asset_server.get_assets()

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_application(self, mock_app):
        """Unit test for get_applications."""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock application
        mock_api_return_value = get_response('application_mock_res.json', True)
        mock_app_res = OktaMockResponse(200, mock_api_return_value)
        mock_app_res.links = {}
        mock_app.return_value = mock_app_res

        # Initiate get_application function
        actual_response = context().asset_server.get_application()

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_application_user(self, mock_app):
        """Unit test for get_application_user."""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock application's user
        mock_api_return_value = get_response('application_usr_res.json', True)
        mock_app_res = OktaMockResponse(200, mock_api_return_value)
        mock_app_res.links = {}
        mock_app.return_value = mock_app_res

        # Initiate get_application function
        actual_response = context().asset_server.get_applications_users([{'id': '234'}])

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_application_error(self, mock_application):
        """Unit test for application."""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock application
        mock_application_res = OktaMockResponse(400, b'Bad Request')
        mock_application.return_value = mock_application_res
        mock_application.links = None

        # Initiate get_application function
        try:
            context().asset_server.get_application()
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_application_user_error(self, mock_val):
        """Unit test for users associated with application."""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock application's user

        mock_val_res = OktaMockResponse(400, b'Bad Request')
        mock_val.return_value = mock_val_res

        # Initiate get_applications_usr function
        try:
            sample_data = [{'id': '123'}]
            context().asset_server.get_applications_users(sample_data)
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_assets_error(self, mock_asset):
        """Unit test for get_assets error"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset
        mock_asset_res = OktaMockResponse(400, b'Bad Request')
        mock_asset.return_value = mock_asset_res

        # Initiate get_assets function
        try:
            context().asset_server.get_assets()
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error
