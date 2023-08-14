import json
import os
import unittest
from unittest.mock import patch
from car_framework.context import Context, context
from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport


class Arguments:
    """Test arguments for automation testing"""

    with open('automation_tests/automation_config.json', 'rb') as json_data:
        args = json.load(json_data)

    CONNECTION_HOST = "test.com"
    CONFIGURATION_AUTH_CLIENT_ID = "xxxxxx"
    CONFIGURATION_AUTH_CLIENT_SECRET = "hjhdxxxxhfo"
    CONNECTION_NAME = args['source']
    CAR_SERVICE_URL = args['car_service_apikey_url']
    CAR_SERVICE_KEY = args['api_key']
    CAR_SERVICE_PASSWORD = args['api_password']
    CAR_SERVICE_URL_FOR_AUTHTOKEN = ""
    CAR_SERVICE_AUTHTOKEN = ""
    export_data_dir = "automation_tests/tests/tmp/car_temp_export_data"
    keep_export_data_dir = "store_true"
    export_data_page_size = 2000
    description = "description"
    debug = None
    CONNECTOR_NAME = args['source']
    CONNECTOR_VERSION = '1.0'


class Payload(object):
    """class for converting the json response as dictionary object"""

    def __init__(self, jdata):
        self.__dict__ = json.loads(jdata)


def get_response(filename, json_format=None):
    """return mock api response"""
    cur_path = os.path.dirname(__file__)
    abs_file_path = cur_path + "/mock_api/" + filename
    with open(abs_file_path, "rb") as json_file:
        response = json_file.read()
        if json_format:
            response = json.loads(response)
        return response


class TestConnector(unittest.TestCase):
    """
    Test Full import, Incremental create, Incremental update, Incremental delete
    """

    @patch('falconpy.discover.Discover.get_hosts')
    @patch('falconpy.discover.Discover.query_hosts')
    @patch('falconpy.discover.Discover.get_applications')
    @patch('falconpy.discover.Discover.query_applications')
    @patch('falconpy.discover.Discover.get_accounts')
    @patch('falconpy.discover.Discover.query_accounts')
    @patch('falconpy.discover.Discover.get_logins')
    @patch('falconpy.discover.Discover.query_logins')
    @patch('falconpy.spotlight_vulnerabilities.SpotlightVulnerabilities.query_vulnerabilities_combined')
    def test_full_import(self, mock_query_combine_vuln, mock_query_logins, mock_get_logins, mock_query_accounts,
                         mock_get_accounts, mock_query_apps, mock_get_apps, mock_query_hosts, mock_get_hosts):
        """unit test for import collection"""

        mock_query_hosts.return_value = get_response('query_hosts_response.json', True)
        mock_get_hosts.return_value = get_response('get_hosts_response.json', True)
        mock_query_apps.return_value = get_response('query_apps_response.json', True)
        mock_get_apps.return_value = get_response('get_apps_response.json', True)
        mock_query_accounts.return_value = get_response('query_accounts_response.json', True)
        mock_get_accounts.return_value = get_response('get_accounts_response.json', True)
        mock_query_logins.return_value = get_response('query_login_response.json', True)
        mock_get_logins.return_value = get_response('get_logins_response.json', True)
        mock_query_combine_vuln.return_value = get_response('query_vuln_combined_response.json', True)
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        asset_id = 'ef21xxxx440d_4141xxxx9623'
        app_name = 'lshw'
        account_name = 'testuser'
        vuln_cve = 'CVE-2013-6438'
        asset = context().car_service.search_collection("asset", "source", context().args.CONNECTOR_NAME, ['external_id'])
        vulns = context().car_service.search_collection("vulnerability", "source",
                                                        context().args.CONNECTOR_NAME, ['external_id'])
        apps = context().car_service.search_collection("application", "source", context().args.CONNECTOR_NAME, ['name'])
        accounts = context().car_service.search_collection("account", "source", context().args.CONNECTOR_NAME, ['name'])
        assert asset_id in str(asset)
        assert app_name in str(apps)
        assert account_name in str(accounts)
        assert vuln_cve in str(vulns)

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
                                       mock_query_hosts, mock_get_hosts):
        """unit test for incremental create and update"""
        # mock host asset, application, account, vulnerability api
        mock_query_hosts.return_value = get_response('query_hosts_response.json', True)
        mock_get_hosts.return_value = get_response('inc_get_hosts_response.json', True)
        mock_query_apps.return_value = get_response('query_apps_response.json', True)
        mock_get_apps.return_value = get_response('inc_get_apps_response.json', True)
        mock_query_accounts.return_value = get_response('query_accounts_response.json', True)
        mock_get_accounts.return_value = get_response('inc_get_accounts_response.json', True)
        mock_query_logins.return_value = get_response('query_login_response.json', True)
        mock_get_logins.return_value = get_response('inc_get_logins_response.json', True)
        mock_query_combine_vuln.return_value = get_response('inc_query_vuln_combined_response.json', True)
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1651375759000, None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()
        # Check the assets pushed in CAR DB
        asset_id = 'ef21xxxx440d_4141xxxx9623'
        ipaddress = '172.0.0.2'
        app_name = 'lshw'
        account_name = 'testuser2'
        vuln_cve = 'CVE-2013-6438'
        asset = context().car_service.search_collection("asset", "source", context().args.CONNECTOR_NAME, ['external_id'])
        vulns = context().car_service.search_collection("vulnerability", "source",
                                                        context().args.CONNECTOR_NAME, ['external_id'])
        apps = context().car_service.search_collection("application", "source", context().args.CONNECTOR_NAME, ['name'])
        accounts = context().car_service.search_collection("account", "source", context().args.CONNECTOR_NAME, ['name'])
        asset_vulnerability = context().car_service.search_collection("asset_vulnerability", "source",
                                                                      context().args.CONNECTOR_NAME, ['asset_id'])
        asset_ipaddress = context().car_service.search_collection("asset_ipaddress", "source",
                                                                  context().args.CONNECTOR_NAME, ['ipaddress_id'])
        assert asset_vulnerability
        assert asset_id in str(asset)
        assert ipaddress in str(asset_ipaddress)
        assert app_name in str(apps)
        assert account_name in str(accounts)
        assert vuln_cve in str(vulns)

    def test_incremental_delete(self):
        """unit test for incremental delete"""
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1651375759000, None)
        context().inc_import.delete_vertices()
        instance_id = 'ef21xxxx440d_4141xxxx9623'
        hostname = 'CROWDST'
        ipaddress = '172.0.0.1'
        application_id = 'ef21xxxx440d_fff0xxxx2200'
        asset = context().car_service.search_collection("asset", "source",
                                                        context().args.CONNECTOR_NAME, ['external_id'])

        assert instance_id not in str(asset)
        asset_hostname = context().car_service.search_collection("asset_hostname", "source",
                                                                 context().args.CONNECTOR_NAME, ['hostname_id'])
        assert hostname not in str(asset_hostname)
        asset_ipaddress = context().car_service.search_collection("asset_ipaddress", "source",
                                                                  context().args.CONNECTOR_NAME, ['ipaddress_id'])
        assert ipaddress not in str(asset_ipaddress)
        asset_application = context().car_service.search_collection("asset_application", "source",
                                                                    context().args.CONNECTOR_NAME, ['application_id'])
        assert application_id not in str(asset_application)
