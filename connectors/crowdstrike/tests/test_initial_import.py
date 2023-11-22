import unittest
from unittest.mock import patch

from tests.test_utils import full_import_initialization, \
    create_vertices_edges, validate_all_handler, get_response


class TestInitialImportFunctions(unittest.TestCase):
    """Unit test for full import"""

    @patch('falconpy.discover.Discover.__init__')
    @patch('falconpy.spotlight_vulnerabilities.SpotlightVulnerabilities.__init__')
    @patch('car_framework.car_service.CarService.get_import_schema')
    @patch('falconpy.discover.Discover.get_hosts')
    @patch('falconpy.discover.Discover.query_hosts')
    @patch('falconpy.discover.Discover.get_applications')
    @patch('falconpy.discover.Discover.query_applications')
    @patch('falconpy.discover.Discover.get_accounts')
    @patch('falconpy.discover.Discover.query_accounts')
    @patch('falconpy.discover.Discover.get_logins')
    @patch('falconpy.discover.Discover.query_logins')
    @patch('falconpy.spotlight_vulnerabilities.SpotlightVulnerabilities.query_vulnerabilities_combined')
    def test_import_collection(self, mock_query_combine_vuln, mock_query_logins, mock_get_logins,
                               mock_query_accounts, mock_get_accounts, mock_query_apps, mock_get_apps,
                               mock_query_hosts, mock_get_hosts, mock_schema, mock_Discover, mock_SpotlightVulnerabilities):
        """unit test for import collection"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset, application, account, vulnerability api
        mock_schema.return_value = get_response('schema.json', True)
        mock_query_hosts.return_value = get_response('query_hosts_response.json', True)
        mock_get_hosts.return_value = get_response('get_hosts_response.json', True)
        mock_query_apps.return_value = get_response('query_apps_response.json', True)
        mock_get_apps.return_value = get_response('get_apps_response.json', True)
        mock_query_accounts.return_value = get_response('query_accounts_response.json', True)
        mock_get_accounts.return_value = get_response('get_accounts_response.json', True)
        mock_query_logins.return_value = get_response('query_login_response.json', True)
        mock_get_logins.return_value = get_response('get_logins_response.json', True)
        mock_query_combine_vuln.return_value = get_response('query_vuln_combined_response.json', True)
        mock_Discover.return_value = None
        mock_SpotlightVulnerabilities.return_value = None

        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    def test_get_new_model_state_id(self):
        """unitest for model_state_id"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        date_id = full_import_obj.get_new_model_state_id()
        assert date_id is not None
