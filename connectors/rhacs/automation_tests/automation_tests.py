import json
import os
import time
import unittest
from unittest.mock import patch
from car_framework.context import Context, context
from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from tests.test_utils import RHACSMockResponse


class Arguments:
    """Test arguments for automation testing"""

    with open('automation_tests/automation_config.json', 'rb') as json_data:
        args = json.load(json_data)

    host = ""  # server name or IP
    port = ""  # Server port
    gateway = ""
    username = ""
    token = ""
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


def get_response(filename, json_format=None):
    """return mock api response"""
    cur_path = os.path.dirname(__file__)
    abs_file_path = cur_path + "/mock_api/" + filename
    with open(abs_file_path, "rb") as json_file:
        response = json_file.read()
        if json_format:
            response = json.loads(response)
        return response


def mocking_apis():
    """ Mocking the API's. """
    mock_roles_obj = get_response('roles.json', True)
    mock_groups_obj = get_response('groups.json', True)
    mock_users_obj = get_response('users.json', True)
    mock_cluster_obj = get_response('clusters.json', True)
    mock_nodes_obj = get_response('nodes.json', True)
    mock_deployements_obj = get_response('deployments.json', True)
    mock_pods_obj = get_response('pods.json', True)
    mock_image_obj = get_response('image.json', True)
    mock_image_obj_json = RHACSMockResponse(200, mock_image_obj)

    mock_obj = [mock_cluster_obj, mock_nodes_obj, mock_deployements_obj,
                mock_pods_obj, mock_image_obj_json, mock_roles_obj,
                mock_groups_obj, mock_users_obj]

    return mock_obj


class TestConnector(unittest.TestCase):
    """
    Test Full import, Incremental create, Incremental update, Incremental delete
    """

    @patch('connector.server_access.AssetServer.get_collection')
    def test_import_collection(self, mock_asset):
        """unit test for import collection"""
        # mock api
        mock_asset.side_effect = mocking_apis()

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        asset_id = '5af50ec2b5228b79aa5ebcc2712241d3816ca2898036b01fd8abe2e21200fc91'
        asset = context().car_service.search_collection("asset", "source", context().args.source, ['external_id'])
        assert asset_id in str(asset)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create(self, mock_api):
        """Test Incremental create"""

        # mock api
        mock_api.side_effect = mocking_apis()

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1651375700000, None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental creation
        ipaddress = '10.111.10.111'
        asset = context().car_service.search_collection("ipaddress", "source", context().args.source, ['external_id'])
        assert ipaddress in str(asset)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_update(self, mock_api):
        """Test Incremental update"""

        # Mock api's
        mock_api.side_effect = mocking_apis()

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1651375759000, None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental update
        vulnerability = 'RHSA-2022:2198'
        asset = context().car_service.search_collection("vulnerability", "source", context().args.source,
                                                        ['external_id'])
        assert vulnerability in str(asset)

    @patch('connector.server_access.AssetServer.get_collection')
    def test_delete_vertices(self, mock_api):
        """Unit test for delete vertices"""

        # mock data source apis
        mock_cve_obj = get_response('cve.json', True)
        mock_images_obj = get_response('images.json', True)
        mock_response = mocking_apis()
        mock_response[3] = get_response('pods_delete.json', True)
        mock_response.extend([mock_cve_obj, mock_images_obj])
        mock_api.side_effect = mock_response

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1651375759000, None)

        # delete vertices
        context().inc_import.delete_vertices()

        # Validate incremental deletion
        time.sleep(5)
        # below container id is deleted from car db
        container_id = '5af50ec2b5228b79aa5ebcc2712241d3816ca2898036b01fd8abe2e21200fc91'
        container = context().car_service.search_collection("container", "source",
                                                            context().args.source, ['external_id'])

        assert container_id not in str(container)
