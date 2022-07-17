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
    def test_get_users(self, mock_user):
        """Unit test for get_users."""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock users API response
        mock_api_return_value = get_response('user_mock_res.json', True)
        mock_user_res = OktaMockResponse(200, mock_api_return_value)
        mock_user_res.links = {}
        mock_user.return_value = mock_user_res

        # Initiate get_users function
        actual_response = context().asset_server.get_users()

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_user_error(self, mock_user):
        """Unit test for get_assets error"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock users API response
        mock_user_res = OktaMockResponse(400, b'Bad Request')
        mock_user.return_value = mock_user_res

        # Initiate get_users function
        try:
            context().asset_server.get_users()
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_applications(self, mock_app):
        """Unit test for get_applications"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock application asset
        mock_api_return_value = get_response('application_mock_res.json', True)
        mock_app_res = OktaMockResponse(200, mock_api_return_value)
        mock_app_res.links = {}
        mock_app.return_value = mock_app_res

        # Initiate get_application function
        actual_response = context().asset_server.get_applications()
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_application_error(self, mock_app):
        """Unit test for get_applications with error."""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock application
        mock_app_res = OktaMockResponse(400, b'Bad Request')
        mock_app.return_value = mock_app_res
        mock_app.links = None

        # Initiate get_application function
        try:
            context().asset_server.get_applications()
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_applications_users(self, mock_apps_users):
        """Unit test for get_applications_users."""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock application's user
        mock_api_return_value = get_response('application_usr_res.json', True)
        mock_apps_users_res = OktaMockResponse(200, mock_api_return_value)
        mock_apps_users_res.links = {}
        mock_apps_users.return_value = mock_apps_users_res

        # Initiate get_applications_users function
        actual_response = context().asset_server.get_applications_users([{'id': '234'}])

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_applications_users_error(self, mock_apps_users):
        """Unit test for users associated with application with error"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock application's users

        mock_apps_users_res = OktaMockResponse(400, b'Bad Request')
        mock_apps_users.return_value = mock_apps_users_res

        # Initiate get_applications_users function
        try:
            sample_data = [{'id': '123'}]
            context().asset_server.get_applications_users(sample_data)
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_systemlogs(self, mock_log):
        """Unit test for get_systemlogs"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock systemlogs
        mock_api_return_value = get_response('logevent_mock_res.json', True)
        mock_log_res = OktaMockResponse(200, mock_api_return_value)
        mock_log_res.links = {}
        mock_log.return_value = mock_log_res

        # Initiate get_systemlogs function
        actual_response = context().asset_server.get_systemlogs()

        assert actual_response is not None
