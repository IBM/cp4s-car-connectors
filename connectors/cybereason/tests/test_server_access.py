import unittest
from unittest.mock import patch
from car_framework.context import context
from connector import server_access
from tests.test_utils import full_import_initialization, get_response,\
                             CybereasonMockResponse


class TestAssetServer(unittest.TestCase):
    """Unit test for server access functions"""

    def test_get_collection(self):
        """unit test for get_collection"""
        try:
            server_access.AssetServer.get_collection('POST',context().asset_server, None)
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
        mock_api_return_value = get_response('assets_api.json', True)
        mock_asset_res = CybereasonMockResponse(200, mock_api_return_value)
        mock_asset.return_value = mock_asset_res

        # Initiate get_assets function
        actual_response = context().asset_server.get_assets()

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_malop_remediation_status(self, mock_asset):
        """Unit test for malop_remediation_status"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock malop remediation status
        mock_api_return_value = get_response('malop_remediation_status.json')
        mock_remediation_res = CybereasonMockResponse(200, mock_api_return_value)
        mock_asset.return_value = mock_remediation_res

        # Initiate get_assets function
        actual_response = context().asset_server.get_malop_remediation_status("11.234567")

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_vulnerabilities(self, mock_vul):
        """Unit test for get_vulnerabilities."""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock vulnerability
        mock_api_return_value = get_response('vulnerability_api.json', True)
        mock_vul_res = CybereasonMockResponse(200, mock_api_return_value)
        mock_vul.return_value = mock_vul_res

        # Initiate get_vulnerabilities function
        actual_response = context().asset_server.get_vulnerabilities()

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_network_interface(self, mock_network):
        """Unit test for get_vulnerabilities."""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock vulnerability
        mock_api_return_value = get_response('network_interface.json', True)
        mock_network_res = CybereasonMockResponse(200, mock_api_return_value)
        mock_network.return_value = mock_network_res

        # Initiate network_interface function
        actual_response = context().asset_server.network_interface(['abc'])

        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_network_interface_error(self, mock_network):
        """Unit test for get_vulnerabilities."""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock vulnerability
        mock_network_res = CybereasonMockResponse(400, b'Bad Request')
        mock_network.return_value = mock_network_res

        # Initiate network_interface function
        try:
            context().asset_server.network_interface(['abc'])
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_vulnerabilities_error(self, mock_vul):
        """Unit test for get_vulnerabilities."""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock vulnerability

        mock_vul_res = CybereasonMockResponse(400, b'Bad Request')
        mock_vul.return_value = mock_vul_res

        # Initiate get_vulnerabilities function
        try:
            context().asset_server.get_vulnerabilities()
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_assets_error(self, mock_asset):
        """Unit test for get_assets. If host asset api having pagination"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset
        mock_asset_res = CybereasonMockResponse(400, b'Bad Request')
        mock_asset.return_value = mock_asset_res

        # Initiate get_assets function
        try:
            context().asset_server.get_assets()
        except Exception as e:
            error = str(e)

        assert 'Bad Request' in error

    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_malop_remediation_status_error(self, mock_asset):
        """Unit test for malop_remediation_status"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock malop remediation status
        mock_remediation_res = CybereasonMockResponse(404, b'Not Found')
        mock_asset.return_value = mock_remediation_res

        # Initiate get_malop_remediation function
        try:
            context().asset_server.get_malop_remediation_status("11.234567")
        except Exception as e:
            error = str(e)

        assert 'Not Found' in error
