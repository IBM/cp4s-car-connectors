import json
import os
import time
import unittest
from unittest.mock import patch, Mock
from car_framework.context import Context, context
from connector import data_handler
from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from tests.test_utils import CybereasonMockResponse


class Arguments:
    """Test arguments for automation testing"""

    with open('automation_tests/automation_config.json', 'rb') as json_data:
        args = json.load(json_data)

    server = ""  # server url
    username = ""  # server username
    password = ""  # server password
    source = args['source']  # source name in car db
    car_service_apikey_url = args['car_service_apikey_url']  # car db url
    api_key = args['api_key']  # car db authentication key
    api_password = args['api_password']  # car db authentication password
    export_data_dir = "automation_tests/tmp/car_temp_export_data"  # export directory
    export_data_page_size = 2000  # page size of export directory
    keep_export_data_dir = "store_true"  # keep the processed files
    api_token = None
    debug = None
    connector_name = args['source']
    gateway = ''
    malop_retention_period = 30


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

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import(self, mock_api):
        """Test full import"""

        mock_asset_res = get_response('assets_api.json', True)
        mock_netwrk_res = get_response('network_interface.json', True)
        mock_vuln_res = get_response('vulnerability_api.json', True)

        mock_asset = CybereasonMockResponse(200, mock_asset_res)
        mock_netwrk = CybereasonMockResponse(200, mock_netwrk_res)
        mock_vuln = CybereasonMockResponse(200, mock_vuln_res)

        mock_api.side_effect = [{'status_code': 200}, mock_asset, mock_netwrk, mock_vuln]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        assets = context().car_service.graph_attribute_search('asset', 'external_id', '13263514')

        assert assets is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create(self, mock_api):
        """Test Incremental create"""

        # mock asset, network, vulnerability api
        inc_create_collections = get_response('inc_create_collections.json', True)
        res_asset = Mock(status_code=200)
        res_asset.content = json.dumps(inc_create_collections["asset"])

        res_network = Mock(status_code=200)
        res_network.content = json.dumps(inc_create_collections["network_interface"])

        mock_header = Mock(status_code=200)

        res_vulnerability = Mock(status_code=200)
        res_vulnerability.content = json.dumps(inc_create_collections["vulnerability"])

        mock_api.side_effect = [mock_header, res_asset, res_network, res_vulnerability]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(data_handler.get_report_time(), None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental creation
        asset = context().car_service.graph_attribute_search('asset', 'external_id', '1673663194.1198775089551518743')
        assert '1673663194.1198775089551518743' in str(asset)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_update(self, mock_api):
        """Test Incremental update"""

        # mock asset, network, vulnerability api
        inc_update_collections = get_response('inc_update_collections.json', True)
        res_asset = Mock(status_code=200)
        res_asset.content = json.dumps(inc_update_collections["asset"])

        res_network = Mock(status_code=200)
        res_network.content = json.dumps(inc_update_collections["network_interface"])

        mock_header = Mock(status_code=200)

        res_vulnerability = Mock(status_code=200)
        res_vulnerability.content = json.dumps(inc_update_collections["vulnerability"])

        mock_api.side_effect = [mock_header, res_asset, res_network, res_vulnerability]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(data_handler.get_report_time(), None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental update
        asset = context().car_service.graph_attribute_search('ipaddress', '_key', '54.174.202.203')
        assert '54.174.202.203' in str(asset)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_delete_vertices(self, mock_api):
        """Unit test for delete vertices"""

        # mock asset, network, vulnerability api
        inc_delete_collections = get_response('inc_delete_collections.json', True)
        res_asset = Mock(status_code=200)
        res_asset.content = json.dumps(inc_delete_collections["asset"])

        res_network = Mock(status_code=200)
        res_network.content = json.dumps(inc_delete_collections["network_interface"])

        mock_header = Mock(status_code=200)

        res_vulnerability = Mock(status_code=200)
        res_vulnerability.content = json.dumps(inc_delete_collections["vulnerability"])

        mock_api.side_effect = [mock_header, res_asset, res_network, res_vulnerability]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(data_handler.get_report_time(), None)

        context().inc_import.delete_vertices()
        # Validate incremental deletion
        time.sleep(1)
        vuln_node = context().car_service.graph_attribute_search(
            'vulnerability', 'external_id', '11.5131751183100962590')
        is_vuln_found = False
        for node in vuln_node:
            if node.get("source") == context().args.source and node.get("external_id") == "11.5131751183100962590":
                is_vuln_found = True
        assert not is_vuln_found
