import json
import os
import unittest
from unittest.mock import patch
from car_framework.context import Context, context
from connector.server_access import AssetServer
from connector.full_import import FullImport
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
    Test Full import
    """

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import(self, mock_api):
        """Test full import"""
        # mock user, application, log api response
        mock_asset_res = get_response('assets_mock_res.json', True)
        mock_app_res = get_response('application_mock_res.json', True)
        mock_app_usr_res = get_response('application_usr_res.json', True)
        mock_logevent_res = get_response('logevent_mock_res.json', True)

        mock_asset = OktaMockResponse(200, mock_asset_res)
        mock_asset.links = {}
        mock_app = OktaMockResponse(200, mock_app_res)
        mock_app.links = {}
        mock_app_usr = OktaMockResponse(200, mock_app_usr_res)
        mock_app_usr.links = {}
        mock_log = OktaMockResponse(200, mock_logevent_res)
        mock_log.links = {'next': {'url': 'okta.com'}}
        mock_log_nextpage = OktaMockResponse(200, [])
        mock_log_nextpage.links = {'next': {'url': 'okta.com'}}

        mock_api.side_effect = [mock_asset, mock_app, mock_app_usr, mock_log, mock_log_nextpage]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        assets = context().car_service.graph_attribute_search('asset', 'external_id', '00uu1y5ok0fhJDDYV696')

        assert assets is not None
