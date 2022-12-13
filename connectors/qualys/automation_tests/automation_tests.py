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
    update_existing_vulnerability_cve = False


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

        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.xml')
        res_app_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_app_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        assets = context().car_service.search_collection("asset", "source", context().args.source, ['external_id'])

        assert assets is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create(self, mock_api):
        """Test Incremental create"""

        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset_inc_create.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.xml')
        res_app_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_app_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(data_handler.get_report_time(), None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental creation
        asset = context().car_service.search_collection("asset", "source", context().args.source, ['external_id'])

        assert '13263515' in str(asset)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_update(self, mock_api):
        """Test Incremental update"""

        # mock host asset and vulnerability api
        res_host_asset = get_response('host_asset_inc_update.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.xml')
        res_app_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_app_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.data_handler.collection_keys = {}
        context().inc_import.data_handler.collections = {}
        context().inc_import.get_data_for_delta(data_handler.get_report_time(), None)

        # incremental update initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental update
        asset = context().car_service.search_collection("asset", "source", context().args.source, ['name'])

        # validate the new asset name updated.
        assert 'ip-177-77-77-777.ec2.internal' in str(asset)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_delete_vertices(self, mock_api):
        """Unit test for import vertices
        doesn't have a vulnerability details"""

        # mock host asset, vulnerability, application and car graph search api
        res_host_asset = get_response('host_asset_inc_delete.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.xml')
        res_app_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_app_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.data_handler.collection_keys = {}
        context().inc_import.data_handler.collections = {}
        context().inc_import.get_data_for_delta('1663784167208.183', None)

        # Initiate delete vertices process
        context().inc_import.delete_vertices()
        time.sleep(10)
        # api_version = '/api/car/v3'
        asset_edge_id = context().args.source + '/' + str(13263514)
        edge_type = "asset_ipaddress"
        result = context().inc_import.query_active_edges(edge_type, asset_edge_id, "ipaddress")
        # Validate the asset_ipaddress edge is inactive for the asset
        assert '11:11:11:11:11:11:11:11' not in str(result)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import_without_sourceinfo(self, mock_api):
        """
        Test full import.
        Host asset API doesn't have a source info
        """
        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset_without_sourceinfo.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.xml')
        res_app_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_app_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        assets = context().car_service.search_collection("asset_geolocation", "source", context().args.source,
                                                         ['asset_id', 'geolocation_id'])
        # validate geolocation in asset
        assert '13263556' not in str(assets)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import_without_osinfo(self, mock_api):
        """
        Test full import.
        Host asset API doesn't have a os info
        """
        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset_without_osinfo.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.xml')
        res_app_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_app_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        assets = context().car_service.search_collection("asset", "source", context().args.source,
                                                         ['external_id', 'description'])
        description = None

        # find the asset description value
        for asset in assets['asset']:
            if asset['external_id'] == '13263555':
                description = asset['description']

        # validate the asset description
        assert description is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import_with_single_vuln(self, mock_api):
        """
        Test full import.
        Vulnerability API have only one detection
        """
        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset_single_vuln.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail_single_detection.xml')
        res_app_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_app_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        vulnerability = context().car_service.search_collection("vulnerability", "source", context().args.source,
                                                         ['external_id'])
        # single vulnerability processed
        assert '101111' in str(vulnerability)
