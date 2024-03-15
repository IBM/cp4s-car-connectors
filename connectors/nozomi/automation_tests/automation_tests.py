import json
import os
import time
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
    CONNECTION_PORT = 443
    CONNECTION_OPTIONS_DATA_RETENTION_PERIOD = 1
    CONFIGURATION_AUTH_KEY_NAME = "xxxxxx"
    CONFIGURATION_AUTH_KEY_TOKEN = "hjhdxxxxhfo"
    CONNECTION_NAME = args['source']
    CAR_SERVICE_URL = args['car_service_apikey_url']
    CAR_SERVICE_KEY = args['api_key']
    CAR_SERVICE_PASSWORD = args['api_password']
    CAR_SERVICE_URL_FOR_AUTHTOKEN = None
    CAR_SERVICE_AUTHTOKEN = None
    store_true = False
    export_data_dir = "tests/tmp/car_temp_export_data"
    keep_export_data_dir = "store_true"
    export_data_page_size = 10000
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


class NozomiMockResponse:
    """class for Okta mock api response"""

    def __init__(self, status_code, content, headers=None, text=None, url=None):
        self.status_code = status_code
        self.headers = headers
        self.text = text
        self.url = url
        self.content = content.encode('utf-8')

    def json(self):
        return json.loads(self.content.decode('utf-8'))


class TestConnector(unittest.TestCase):
    """
    Test Full import, Incremental create, Incremental update, Incremental delete
    """

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import(self, mock_results):
        """unit test for import collection"""

        # mock data source API responses
        login_response = json.dumps(get_response('login_response.json', True))
        query_assets = json.dumps(get_response('query_assets.json', True))
        query_sensors = json.dumps(get_response('query_sensors.json', True))
        query_nodes = json.dumps(get_response('query_nodes.json', True))
        query_software_list = json.dumps(get_response('query_softwares_list.json', True))
        query_asset_softwares = json.dumps(get_response('query_asset_softwares.json', True))
        query_vulnerabilities = json.dumps(get_response('query_vulnerabilities.json', True))
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        mock_results.side_effect = [NozomiMockResponse(200, login_response, headers={'Authorization': 'bearer xxxxxx'}),
                                    NozomiMockResponse(200, query_assets),
                                    NozomiMockResponse(200, query_sensors),
                                    NozomiMockResponse(200, query_nodes),
                                    NozomiMockResponse(200, query_software_list),
                                    NozomiMockResponse(200, query_asset_softwares),
                                    NozomiMockResponse(200, query_vulnerabilities)]
        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        asset_id = '0093xxxx-xxxx-xxxx-xxxx-xxxxxxxxb98c'
        app_id = 'CP8811 1.5.4.0:10.3.1'
        vuln_cve = 'CVE-2023-25619'
        time.sleep(120)
        vulns = context().car_service.search_collection("vulnerability", "source",
                                                        context().args.CONNECTOR_NAME, ['name'])
        asset = context().car_service.search_collection("asset", "source",
                                                        context().args.CONNECTOR_NAME, ['external_id'])
        apps = context().car_service.search_collection("application", "source",
                                                       context().args.CONNECTOR_NAME, ['external_id'])

        assert asset_id in str(asset)
        assert app_id in str(apps)
        assert vuln_cve in str(vulns)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create_update(self, mock_results):
        """unit test for incremental create and update"""
        # mock host asset, application, nodes, sensors, vulnerability queries
        login_response = json.dumps(get_response('login_response.json', True))
        query_assets = json.dumps(get_response('inc_query_assets.json', True))
        query_sensors = json.dumps(get_response('query_sensors.json', True))
        query_nodes = json.dumps(get_response('inc_query_nodes.json', True))
        query_software_list = json.dumps(get_response('query_softwares_list.json', True))
        query_asset_softwares = json.dumps(get_response('inc_query_asset_softwares.json', True))
        query_vulnerabilities = json.dumps(get_response('inc_query_vulnerabilities.json', True))
        mock_results.side_effect = [NozomiMockResponse(200, login_response, headers={'Authorization': 'bearer xxxxxx'}),
                                    NozomiMockResponse(200, query_assets),
                                    NozomiMockResponse(200, query_sensors),
                                    NozomiMockResponse(200, query_nodes),
                                    NozomiMockResponse(200, query_software_list),
                                    NozomiMockResponse(200, query_asset_softwares),
                                    NozomiMockResponse(200, query_vulnerabilities)]
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1651375759000, None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()
        # Check the assets pushed in CAR DB
        asset_id = '0093xxxx-xxxx-xxxx-xxxx-xxxxxxxxb98e'
        ipaddress = '1.1.1.5'
        app_id = 'CP8812 1.5.4.0:10.3.2'
        vuln_cve = 'CVE-2023-25629'
        time.sleep(120)
        asset = context().car_service.search_collection("asset", "source",
                                                        context().args.CONNECTOR_NAME, ['external_id'])
        inc_vulns = context().car_service.search_collection("vulnerability", "source",
                                                            context().args.CONNECTOR_NAME, ['name', 'external_id'])
        apps = context().car_service.search_collection("application", "source",
                                                       context().args.CONNECTOR_NAME, ['external_id'])
        asset_vulnerability = context().car_service.search_collection("asset_vulnerability", "source",
                                                                      context().args.CONNECTOR_NAME, ['asset_id'])
        asset_ipaddress = context().car_service.search_collection("asset_ipaddress", "source",
                                                                  context().args.CONNECTOR_NAME, ['ipaddress_id'])
        assert asset_vulnerability
        assert asset_id in str(asset)
        assert ipaddress in str(asset_ipaddress)
        assert app_id in str(apps)
        assert vuln_cve in str(inc_vulns)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_delete(self, mock_results):
        """unit test for incremental delete"""
        login_response = json.dumps(get_response('login_response.json', True))
        query_vulnerabilities = json.dumps(get_response('query_vulnerabilities.json', True))
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1851375759000, None)
        mock_results.side_effect = [NozomiMockResponse(200, login_response, headers={'Authorization': 'bearer xxxxxx'}),
                                    NozomiMockResponse(200, query_vulnerabilities)]
        context().inc_import.delete_vertices()
        instance_id = '0093xxxx-xxxx-xxxx-xxxx-xxxxxxxxb98e'
        ipaddress = '1.1.1.5'
        application_id = '00cfxxxx-xxxx-xxxx-xxxx-2xxxxxxxe245'
        asset = context().car_service.search_collection("asset", "source",
                                                        context().args.CONNECTOR_NAME, ['external_id'])

        assert instance_id not in str(asset)
        asset_ipaddress = context().car_service.search_collection("asset_ipaddress", "source",
                                                                  context().args.CONNECTOR_NAME, ['ipaddress_id'])
        assert ipaddress not in str(asset_ipaddress)
        asset_application = context().car_service.search_collection("asset_application", "source",
                                                                    context().args.CONNECTOR_NAME, ['application_id'])
        assert application_id not in str(asset_application)
