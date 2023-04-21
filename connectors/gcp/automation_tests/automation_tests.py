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

    host = ""
    client_email = ""
    certificate = ""
    page_size = 1
    source = "GCP"
    car_service_apikey_url = args['car_service_apikey_url']
    api_key = args['api_key']
    api_password = args['api_password']
    car_service_token_url = ""
    api_token = ""
    export_data_dir = "automation_tests/tests/tmp/car_temp_export_data"
    keep_export_data_dir = "store_true"
    export_data_page_size = 2000
    description = "description"
    debug = None
    connector_name = args['source']
    version = '1.0'


class Payload(object):
    """class for converting the json response as dictionary object"""

    def __init__(self, jdata):
        self.__dict__ = json.loads(jdata)


def project_response():
    """mocking response of project_list"""

    response = Payload(json.dumps(get_response('project_list.json', True)))
    return response


def vuln_response():
    """mocking the vulnerability response"""

    response = get_response('os_inv_response.json', True)
    scc_response = response['scc_response']
    for obj in scc_response:
        scc_find = Payload(json.dumps(obj))
        scc_find.finding = Payload(json.dumps(obj['finding']))
    scc_response[0] = scc_find
    return response


def mock_response():
    # Mock VM instance,OS and Vulnerability responses
    vm_instance = get_response('vm_instances.json', True)
    vm_instance_os_pkgs = get_response('vm_instance_os_pkgs.json', True)
    vm_instance_os_vuln = get_response('vm_instance_os_vuln.json', True)
    web_app = get_response('web_app.json', True)
    web_app_service = get_response('web_app_service.json', True)
    web_app_service_version = get_response('web_app_service_version.json', True)
    mock_obj = [vm_instance, vm_instance_os_pkgs, vm_instance_os_vuln,
                web_app, web_app_service, web_app_service_version]
    return mock_obj


def mock_history_response():
    # Mock get_asset_history responses
    vm_instance = get_response('vm_instance_history.json', True)
    vm_instance_os_pkgs = get_response('vm_instance_os_pkgs_history.json', True)
    vm_instance_os_vuln = get_response('vm_instance_os_vuln_history.json', True)
    vm_instance_update = get_response('vm_instance_update_history.json', True)
    vm_instance_os_pkgs_updated = get_response('vm_instance_os_pkgs_history.json', True)
    vm_instance_os_vuln_updated = get_response('vm_instance_os_vuln_history.json', True)
    web_app = get_response('web_app.json', True)
    web_app_service = get_response('web_app_service.json', True)
    web_app_service_version = get_response('web_app_service_version.json', True)
    mock_obj = [vm_instance, vm_instance_os_pkgs, vm_instance_os_vuln,
                vm_instance_update, vm_instance_os_pkgs_updated, vm_instance_os_vuln_updated,
                web_app, web_app_service, web_app_service_version]
    return mock_obj


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

    @patch('connector.server_access.AssetServer.get_vulnerabilities')
    @patch('connector.server_access.AssetServer.get_asset_list')
    @patch('google.oauth2.service_account.Credentials.from_service_account_info')
    @patch('google.cloud.resourcemanager_v3.SearchProjectsRequest')
    @patch('google.cloud.resourcemanager_v3.ProjectsClient.search_projects')
    def test_full_import(self, mock_search_project, mock_search_request, mock_credentials, mock_asset_list,
                         mock_vul):
        """unit test for import collection"""

        mock_credentials.return_value = '123'
        mock_search_request.return_value = True
        mock_search_project.return_value = [project_response()]
        mock_asset_list.side_effect = mock_response()
        mock_vul.side_effect = [get_response('scc_response.json', True)]

        Context(Arguments)
        context().asset_server = AssetServer()
        context().full_importer = FullImport()

        # full import initiation
        context().full_importer.run()

        # Check the assets pushed in CAR DB
        asset_id = '6000000000000000001'
        web_app_service = "apps/dummyapp/services/app1"
        asset = context().car_service.search_collection("asset", "source", context().args.source, ['external_id'])
        assert asset_id in str(asset)
        assert web_app_service in str(asset)

    @patch('connector.server_access.AssetServer.get_asset_history')
    @patch('connector.server_access.AssetServer.get_logs')
    @patch('connector.server_access.AssetServer.get_vulnerabilities')
    @patch('connector.server_access.AssetServer.get_asset_list')
    @patch('google.oauth2.service_account.Credentials.from_service_account_info')
    @patch('google.cloud.resourcemanager_v3.SearchProjectsRequest')
    @patch('google.cloud.resourcemanager_v3.ProjectsClient.search_projects')
    def test_increment_create_update(self, mock_search_project, mock_search_request, mock_credentials, mock_asset_list,
                                     mock_vul, mock_logs, mock_asset_history):
        """unit test for incremental create and update"""

        mock_credentials.return_value = '123'
        mock_search_request.return_value = True
        mock_search_project.return_value = [project_response()]
        mock_asset_list.side_effect = mock_response()
        mock_vul.side_effect = [get_response('scc_response.json', True)]
        mock_asset_history.side_effect = mock_history_response()
        # Mock logs:
        mock_logs.side_effect = [get_response('vm_create_log.json', True),
                                 get_response('vm_update_log.json', True),
                                 get_response('vm_create_log.json', True),
                                 [],
                                 get_response('web_app_update_log.json', True),
                                 get_response('web_app_service_version_log.json', True)]
        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1651375759000, None)

        # incremental creation initiation
        context().inc_import.import_vertices()
        context().inc_import.import_edges()

        # Validate the incremental update
        cve = 'CVE-2022-2923'
        vulnerability = context().car_service.search_collection("vulnerability", "source", context().args.source,
                                                                ['external_id'])
        assert cve in str(vulnerability)

    @patch('connector.server_access.AssetServer.get_vulnerabilities')
    @patch('google.oauth2.service_account.Credentials.from_service_account_info')
    @patch('google.cloud.resourcemanager_v3.SearchProjectsRequest')
    @patch('google.cloud.resourcemanager_v3.ProjectsClient.search_projects')
    def test_increment_delete(self, mock_search_project, mock_search_request,
                              mock_credentials, mock_vuln):
        """unit test for incremental delete"""
        mock_credentials.return_value = '123'
        mock_search_request.return_value = True
        mock_search_project.return_value = [project_response()]
        mock_vuln.return_value = [get_response('scc_response.json', True)]

        # Initialization
        Context(Arguments)
        context().asset_server = AssetServer()
        context().inc_import = IncrementalImport()
        context().inc_import.get_data_for_delta(1651375759000, None)
        context().inc_import.projects = ['dummyproj']
        context().inc_import.deleted_vertices = \
            {'asset': {'compute.googleapis.com/projects/dummyproj/zones/us-central1-a/instances/6000000000000000002'}}
        context().inc_import.delete_vertices()

        # Validate incremental deletion
        time.sleep(1)
        # below asset id is deleted from car db
        instance_id = 'compute.googleapis.com/projects/dummyproj/zones/us-central1-a/instances/6000000000000000002'
        asset = context().car_service.search_collection("asset", "source",
                                                        context().args.source, ['external_id'])

        assert instance_id not in str(asset)
