import json
import os
import time
import unittest
from unittest.mock import patch
from car_framework.context import Context, context
from connector import data_handler
from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from tests.test_utils import OktaMockResponse


class Arguments:
    """Test arguments for automation testing"""

    with open('automation_tests/automation_config.json', 'rb') as json_data:
        args = json.load(json_data)

    host = "okta.com"  # server url
    auth_token = ""  # server password
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
    version = "1.0"


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
        # mock user, application, log api response
        mock_app_res = get_response('application_mock_res.json', True)
        mock_user_res = get_response('user_mock_res.json', True)
        mock_app_usr_res = get_response('application_usr_res.json', True)
        mock_logevent_res = get_response('logevent_mock_res.json', True)

        mock_user = OktaMockResponse(200, mock_user_res)
        mock_user.links = {}

        mock_app = OktaMockResponse(200, mock_app_res)
        mock_app.links = {}

        mock_app_usr = OktaMockResponse(200, mock_app_usr_res)
        mock_app_usr.links = {}
        mock_log = OktaMockResponse(200, mock_logevent_res)
        mock_log.links = {}

        mock_api.side_effect = [mock_user, mock_app, mock_app_usr, mock_log]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        asset_node = context().car_service.search_collection(
            'asset', 'external_id', '0oau1u58hh0PLgyax696', ['external_id', "source"])
        is_asset_found = False
        for node in asset_node['asset']:
            if node.get("source") == context().args.source and '0oau1u58hh0PLgyax696' in node.get("external_id"):
                is_asset_found = True
        assert is_asset_found

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create(self, mock_api):
        """Test Incremental create"""

        # mock application, user  api
        inc_create_collections = get_response('inc_create_collections.json', True)

        mock_user = OktaMockResponse(200, inc_create_collections["asset"])
        mock_user.links = {}

        mock_app = OktaMockResponse(200, inc_create_collections["application"])
        mock_app.links = {}

        mock_app_user = OktaMockResponse(200, inc_create_collections["app_user"])
        mock_app_user.links = {}

        mock_events = OktaMockResponse(200, inc_create_collections["events"])
        mock_events.links = {}
        mock_events_disable = OktaMockResponse(200, [])
        mock_events_disable.links = {}

        mock_api.side_effect = [mock_user, mock_app, mock_app_user,
                                mock_events, mock_user, mock_events_disable, mock_events_disable]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(data_handler.get_report_time(), None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental creation
        asset_node = context().car_service.search_collection(
            'asset', 'external_id', '0oau1u58hh0PLgyax696', ['external_id', "source"])
        is_asset_found = False
        for node in asset_node['asset']:
            if node.get("source") == context().args.source and "0oau1u58hh0PLgyax696" in node.get("external_id"):
                is_asset_found = True
        assert is_asset_found

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_update(self, mock_api):
        """Test Incremental update"""

        # mock application, user, app_uer api
        inc_update_collections = get_response('inc_update_collections.json', True)

        mock_user = OktaMockResponse(200, inc_update_collections["asset"])
        mock_user.links = {}

        mock_app = OktaMockResponse(200, inc_update_collections["application"])
        mock_app.links = {}

        mock_app_user = OktaMockResponse(200, inc_update_collections["app_user"])
        mock_app_user.links = {}

        mock_events = OktaMockResponse(200, inc_update_collections["events"])
        mock_events.links = {}
        mock_events_disable = OktaMockResponse(200, [])
        mock_events_disable.links = {}

        mock_api.side_effect = [mock_user, mock_app, mock_app_user,
                                mock_events, mock_user,
                                mock_events_disable]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(data_handler.get_report_time(), None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental update
        asset_node = context().car_service.search_collection(
            'asset', 'external_id', '0oau1u58hh0PLgyax696', ['external_id', "source"])
        is_asset_found = False
        for node in asset_node['asset']:
            if node.get("source") == context().args.source and "0oau1u58hh0PLgyax696" in node.get("external_id"):
                is_asset_found = True
        assert is_asset_found

    @patch('connector.server_access.AssetServer.get_systemlogs')
    @patch('connector.server_access.AssetServer.get_asset_collections')
    def test_incremental_delete_vertices(self, mock_api, mock_events):
        """Unit test for delete vertices"""

        # mock application, user api
        inc_delete_collections = get_response('inc_delete_collections.json', True)

        # Mock get_model_state_delta return values:
        delta = {'user': [], 'application': [], 'client': []}
        mock_api.return_value = delta

        mock_events.side_effect = [inc_delete_collections['user'], inc_delete_collections['user'],
                                   inc_delete_collections['application']]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(data_handler.get_report_time(), None)

        context().inc_import.delete_vertices()
        # Validate incremental deletion
        time.sleep(1)
        app_node = context().car_service.search_collection(
            'application', 'external_id', '0oa4rs2ulp6DmX0fP5d7', ['external_id', "source"])
        is_app_found = False
        for node in app_node['application']:
            if node.get("source") == context().args.source and "0oa4rs2ulp6DmX0fP5d7" in node.get("external_id"):
                is_app_found = True
        assert not is_app_found
