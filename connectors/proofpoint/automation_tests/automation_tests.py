import unittest
import time
import json
from unittest.mock import patch
from car_framework.context import Context, context
from automation_tests.convert_from_json import JsonResponse
from connector import data_handler
from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport


class Arguments:
    """Test arguments for automation testing"""

    with open('automation_tests/automation_config.json', 'rb') as json_data:
        args = json.load(json_data)

    server = ""  # proofpoint server url
    username = ""  # Proofpoint server username
    password = ""  # Proofpoint server password
    source = args['source']  # source name in car db
    car_service_apikey_url = args['car_service_apikey_url']  # car db url
    api_key = args['api_key']  # car db authentication key
    api_password = args['api_password']  # car db authentication password
    export_data_dir = "automation_tests/tmp/car_temp_export_data"  # export directory
    export_data_page_size = 2000  # page size of export directory
    keep_export_data_dir = "store_true" # keep the processed files
    api_token = None
    debug = None


class TestProofPointConnector(unittest.TestCase):
    """
    Test Full import, Incremental create, Incremental update, Incremental delete
    """

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import(self, mock_api):
        """Test full import"""

        # Mock api configurations
        mock_siem_api = JsonResponse(200, 'siem_api.json').json()
        mock_people_api = JsonResponse(200, 'people_api.json').json()
        mock_api.side_effect = [mock_siem_api, mock_people_api]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().full_importer.config['parameter']['interval_days'] = 0.01

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        assets = context().car_service.graph_attribute_search('asset', 'external_id',
                                                              'subashuser@galaxyabcd.com')

        assert assets is not None

    def test_incremental_create(self):
        """Test Incremental create"""

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.last_model_state_id = data_handler.get_report_time()

        # Mock api configurations
        context().inc_import.delta = JsonResponse(200, 'inc_creation.json').json()
        context().inc_import.active_vulnerability = ['ecb8e938619ad370e070ff7e8426b89cb57f1861b736ac5991fa46c34b902f35']

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental creation
        user = context().car_service.graph_search('vulnerability',
                                                  'ddd8e938619ad370e070ff7e8426b89cb57f1861b736ac5991fa46c34b902f35')
        assert user is not None

    def test_incremental_update(self):
        """Test Incremental update"""

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.last_model_state_id = data_handler.get_report_time()

        # Mock api configurations
        context().inc_import.delta = JsonResponse(200, 'inc_update.json').json()
        context().inc_import.active_vulnerability = ['ddd8e938619ad370e070ff7e8426b89cb57f1861b736ac5991fa46c34b902f35',
                                                     'ecb8e938619ad370e070ff7e8426b89cb57f1861b736ac5991fa46c34b902f35']

        # incremental update initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental update
        vulnerabilities = context().car_service.graph_search('vulnerability',
                                  'ecb8e938619ad370e070ff7e8426b89cb57f1861b736ac5991fa46c34b902f35')

        assert "'modified': '2021-09-29T05:17:21.000Z'" in str(vulnerabilities)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_delete(self, mock_api):
        """Test incremental delete"""

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()

        # Mock api configurations
        mock_api.return_value = JsonResponse(200, 'deleted_threat.json').json()

        # Incremental deletion initiation
        context().inc_import.delete_vertices()
        time.sleep(10)

        # Check the active records after deletions
        active_vulnerabilities = context().car_service.graph_attribute_search('vulnerability', 'source',
                                                                              context().args.source)
        assert len(active_vulnerabilities) == 0
