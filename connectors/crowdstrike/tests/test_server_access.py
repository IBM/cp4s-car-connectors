import unittest
from unittest.mock import patch

from car_framework.context import context
from tests.test_utils import full_import_initialization, get_response


class TestAssetServer(unittest.TestCase):
    """Unit test for server access functions"""

    @patch('falconpy.discover.Discover.query_hosts')
    def test_connection(self, mock_query_hosts):
        """unit test for test connection"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_query_hosts.return_value = get_response('query_hosts_response.json', True)
        actual_response = context().asset_server.test_connection()
        assert actual_response is not None

    @patch('falconpy.discover.Discover.query_hosts')
    def test_connection_with_error(self, mock_query_hosts):
        """unit test for test connection failure"""
        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_query_hosts.return_value = get_response('api_auth_error.json', True)
        actual_response = context().asset_server.test_connection()
        assert actual_response == 1

    @patch('falconpy.discover.Discover.get_hosts')
    @patch('falconpy.discover.Discover.query_hosts')
    def test_get_hosts(self, mock_query_hosts, mock_get_hosts):
        """unit test for get_hosts"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_query_hosts.return_value = get_response('query_hosts_response.json', True)
        mock_get_hosts.return_value = get_response('get_hosts_response.json', True)
        host_list = context().asset_server.get_hosts()
        assert host_list is not None

    @patch('falconpy.discover.Discover.get_hosts')
    @patch('falconpy.discover.Discover.query_hosts')
    def test_get_hosts_with_error(self, mock_query_hosts, mock_get_hosts):
        """unit test for get_hosts"""
        error_response = None
        try:
            full_import_obj = full_import_initialization()
            full_import_obj.create_source_report_object()
            mock_query_hosts.return_value = get_response('api_auth_error.json', True)
            mock_get_hosts.return_value = get_response('get_hosts_response.json', True)
            context().asset_server.get_hosts()
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('falconpy.discover.Discover.get_applications')
    @patch('falconpy.discover.Discover.query_applications')
    def test_get_applications(self, mock_query_apps, mock_get_apps):
        """unit test for get_applications"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_query_apps.return_value = get_response('query_apps_response.json', True)
        mock_get_apps.return_value = get_response('get_apps_response.json', True)
        apps_list = context().asset_server.get_applications()
        assert apps_list is not None

    @patch('falconpy.discover.Discover.get_applications')
    @patch('falconpy.discover.Discover.query_applications')
    def test_get_applications_with_error(self, mock_query_apps, mock_get_apps):
        """unit test for get_applications with error"""
        error_response = None
        try:
            full_import_obj = full_import_initialization()
            full_import_obj.create_source_report_object()
            mock_query_apps.return_value = get_response('api_auth_error.json', True)
            mock_get_apps.return_value = get_response('get_apps_response.json', True)
            context().asset_server.get_applications()
        except Exception as e:
            error_response = str(e)
        assert error_response is not None

    @patch('falconpy.discover.Discover.get_accounts')
    @patch('falconpy.discover.Discover.query_accounts')
    def test_get_accounts(self, mock_query_accounts, mock_get_accounts):
        """unit test for get_accounts"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_query_accounts.return_value = get_response('query_accounts_response.json', True)
        mock_get_accounts.return_value = get_response('get_accounts_response.json', True)
        account_list = context().asset_server.get_accounts()
        assert account_list is not None

    @patch('falconpy.discover.Discover.get_accounts')
    @patch('falconpy.discover.Discover.query_accounts')
    def test_get_accounts_with_error(self, mock_query_accounts, mock_get_accounts):
        """unit test for get_accounts with error"""
        error_response = None
        try:
            full_import_obj = full_import_initialization()
            full_import_obj.create_source_report_object()
            mock_query_accounts.return_value = get_response('api_auth_error.json', True)
            mock_get_accounts.return_value = get_response('get_accounts_response.json', True)
            context().asset_server.get_accounts()
        except Exception as ex:
            error_response = str(ex)
        assert error_response is not None

    @patch('falconpy.discover.Discover.get_logins')
    @patch('falconpy.discover.Discover.query_logins')
    def test_get_logins(self, mock_query_logins, mock_get_logins):
        """unit test for get_logins"""
        accounts = []
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_query_logins.return_value = get_response('query_login_response.json', True)
        mock_get_logins.return_value = get_response('get_logins_response.json', True)
        logins_list = context().asset_server.get_logins(accounts)
        assert logins_list is not None

    @patch('falconpy.discover.Discover.get_logins')
    @patch('falconpy.discover.Discover.query_logins')
    def test_get_logins_with_error(self, mock_query_logins, mock_get_logins):
        """unit test for get_logins with error"""
        error_response = None
        try:
            accounts = ['efxxxxfw']
            full_import_obj = full_import_initialization()
            full_import_obj.create_source_report_object()
            mock_query_logins.return_value = get_response('api_auth_error.json', True)
            mock_get_logins.return_value = get_response('get_logins_response.json', True)
            context().asset_server.get_logins(accounts)
        except Exception as ex:
            error_response = str(ex)
        assert error_response is not None

    @patch('falconpy.spotlight_vulnerabilities.SpotlightVulnerabilities.query_vulnerabilities_combined')
    def test_get_vulnerabilities(self, mock_query_combine_vuln):
        """unit test for get_vulnerabilities"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        mock_query_combine_vuln.return_value = get_response('query_vuln_combined_response.json', True)
        vuln_list = context().asset_server.get_vulnerabilities()
        assert vuln_list is not None

    @patch('falconpy.spotlight_vulnerabilities.SpotlightVulnerabilities.query_vulnerabilities_combined')
    def test_get_vulnerabilities_error(self, mock_query_combine_vuln):
        """unit test for get_vulnerabilities with error"""
        error_response = None
        try:
            full_import_obj = full_import_initialization()
            full_import_obj.create_source_report_object()
            mock_query_combine_vuln.return_value = get_response('api_auth_error.json', True)
            context().asset_server.get_vulnerabilities()
        except Exception as ex:
            error_response = str(ex)
        assert error_response is not None
