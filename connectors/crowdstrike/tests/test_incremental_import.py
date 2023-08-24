import unittest
from unittest.mock import patch

from tests.test_utils import inc_import_initialization, create_vertices_edges, \
    validate_all_handler, get_response


class TestIncrementalImportFunctions(unittest.TestCase):
    """Unit test for incremental import"""

    @patch('car_framework.car_service.CarService.search_collection')
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
    def test_incremental_create_update(self, mock_query_combine_vuln, mock_query_logins, mock_get_logins,
                                       mock_query_accounts, mock_get_accounts, mock_query_apps, mock_get_apps,
                                       mock_query_hosts, mock_get_hosts, mock_schema, mock_collections):
        """unit test for incremental create and update"""
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        inc_import_obj.get_data_for_delta(1651375759000, None)
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
        collections = get_response('car_search_collection.json', True)
        mock_collections.side_effect = [collections['asset_hostname'], collections['asset_ipaddress']]
        actual_response = create_vertices_edges(inc_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.delete')
    @patch('car_framework.car_service.CarService.query_graphql')
    def test_increment_delete(self, mock_search, mock_delete):
        """unit test for incremental delete"""
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        inc_import_obj.update_edge = []
        inc_import_obj.get_data_for_delta(1662009569000, None)
        search_res = get_response('car_graphql_search.json', True)
        mock_search.side_effect = [search_res['asset'], search_res['account'], search_res['application']]
        # Mock Edge patch response
        mock_delete.return_value = {'status': 'success'}
        assert inc_import_obj.delete_vertices() is None