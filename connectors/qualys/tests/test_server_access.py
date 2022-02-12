import unittest
from unittest.mock import patch, Mock
from car_framework.context import context
from connector import full_import, server_access, data_handler
from tests.test_utils import full_import_initialization, get_response


class TestAssetServer(unittest.TestCase):
    """Unit test for server access functions"""

    def test_get_collection(self):
        """unit test for get_collection"""
        full_import_initialization()
        full_import.FullImport()
        error_response = None
        try:
            server_access.AssetServer.get_collection(context().asset_server, None)
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_assets_with_pagination(self, mock_api):
        """Unit test for get_assets. If host asset api having pagination"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset
        host_asset_page_1 = get_response('host_asset_pagination.json', True)
        host_asset_page_2 = get_response('host_asset.json', True)

        mock_host_asset_page_1 = Mock(status_code=200)
        mock_host_asset_page_1.json.return_value = host_asset_page_1

        mock_host_asset_page_2 = Mock(status_code=200)
        mock_host_asset_page_2.json.return_value = host_asset_page_2

        mock_api.side_effect = [mock_host_asset_page_1, mock_host_asset_page_2]

        # Initiate get_assets function
        actual_response = context().asset_server.get_assets(str(data_handler.get_report_time()))

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_vulnerabilities(self, mock_api):
        """Unit test for get_vulnerabilities.
         If vulnerability api having pagination."""

        # mock vulnerability api
        vuln_page_1 = get_response('vulnerability_detail_pagination.json')
        vuln_page_2 = get_response('vulnerability_detail.json')

        mock_vuln_page_1 = Mock(status_code=200)
        mock_vuln_page_1.text = vuln_page_1

        mock_vuln_page_2 = Mock(status_code=200)
        mock_vuln_page_2.text = vuln_page_2

        mock_api.side_effect = [mock_vuln_page_1, mock_vuln_page_2]

        # Initiate get_vulnerabilities function
        actual_response = context().asset_server.get_vulnerabilities()

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_assets_with_error(self, mock_api):
        """Unit test for get_assets. If invalid credentials provided"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset api
        host_asset = get_response('host_asset_error.json', True)

        mock_host_asset = Mock(status_code=404)
        mock_host_asset.json.return_value = host_asset

        mock_api.side_effect = [mock_host_asset]

        try:
            # initiate the get_assets
            context().asset_server.get_assets(None)
        except Exception as e:
            error = str(e)

        assert 'Authentication failed' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_vulnerabilities_with_error(self, mock_api):
        """Unit test for get_vulnerabilities. If invalid credentials provided"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset api
        host_asset = get_response('vulnerability_detail_error.json')

        mock_host_asset = Mock(status_code=404)
        mock_host_asset.text = host_asset
        mock_api.side_effect = [mock_host_asset]

        try:
            # initiate get_vulnerabilities
            context().asset_server.get_vulnerabilities()
        except Exception as e:
            error = str(e)

        assert 'Bad Login/Password' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_application_with_error(self, mock_api):
        """Unit test for get_applications. If invalid credentials provided"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset api
        application = get_response('application_detail_error.json', True)

        mock_header = Mock(status_code=200)
        mock_header.text = 'abcd'

        mock_application = Mock(status_code=404)
        mock_application.json.return_value = application
        mock_api.side_effect = [mock_header, mock_application]

        try:
            # initiate get_applications
            context().asset_server.get_applications(None)
        except Exception as e:
            error = str(e)

        assert 'Unauthorized' in error
