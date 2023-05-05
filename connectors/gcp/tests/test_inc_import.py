import unittest
from unittest.mock import patch

from tests.test_utils import inc_import_initialization, create_vertices_edges, \
    validate_all_handler, get_response, \
    project_response, mock_response, mock_history_response


@patch('car_framework.car_service.CarService.get_import_schema')
@patch('connector.server_access.AssetServer.get_asset_history')
@patch('car_framework.car_service.CarService.delete')
@patch('car_framework.car_service.CarService.edge_patch')
@patch('car_framework.car_service.CarService.search_collection')
@patch('connector.server_access.AssetServer.get_vulnerabilities')
@patch('connector.server_access.AssetServer.get_asset_list')
@patch('google.oauth2.service_account.Credentials.from_service_account_info')
@patch('google.cloud.resourcemanager_v3.SearchProjectsRequest')
@patch('google.cloud.resourcemanager_v3.ProjectsClient.search_projects')
class TestIncrementalImportFunctions(unittest.TestCase):
    """Unit test for incremental import"""

    @patch('googleapiclient.discovery.build')
    @patch('car_framework.car_service.CarService.query_graphql')
    @patch('connector.server_access.AssetServer.get_logs')
    def test_incremental_create_update(self, mock_logs, mock_query_result, mock_discovery, *patchs):
        """unit test for incremental create and update"""

        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        patchs[2].return_value = '123'
        patchs[1].return_value = True
        patchs[0].return_value = [project_response()]
        patchs[3].side_effect = [get_response('web_app.json', True)]
        patchs[4].side_effect = [get_response('scc_response.json', True)]
        patchs[8].side_effect = mock_history_response()
        patchs[9].return_value = get_response('schema.json', True)
        # Mock logs:
        mock_logs.side_effect = [get_response('gke_incremental_log.json', True),
                                 get_response('gke_workload_vulns.json', True),
                                 get_response('vm_create_log.json', True),
                                 get_response('vm_update_log.json', True),
                                 get_response('vm_create_log.json', True),
                                 [],
                                 get_response('web_app_service_version_log.json', True),
                                 get_response('sql_incremental_log.json', True)]
        # sql db and user details
        mock_discovery.return_value.databases.return_value.list.return_value.execute.return_value = \
            get_response('sql_db.json', True)
        mock_discovery.return_value.users.return_value.list.return_value.execute.return_value = \
            get_response('sql_user.json', True)
        # mock graphql search
        mock_query_result.side_effect = [{'data': {'asset': [{'external_id': 'cluster2'}]}},
                                         {'data': {'asset': [{'external_id': 'cluster1'}]}},
                                         {'data': {'asset_application': [{'application_id': 'source/nginx-1'}]}},
                                         {'data': {'asset_database': [{'database_id': 'source/db1-1'}]}},
                                         {'data': {'asset_account': [{'account_id': 'source/user1-1'}]}}]
        # mock search collection
        mock_collections = get_response('car_edges.json', True)
        patchs[5].side_effect = [mock_collections['asset_hostname'], mock_collections['asset_ipaddress'],
                                 mock_collections['asset_application'], mock_collections['asset_vulnerability']]
        inc_import_obj.get_data_for_delta(1651375759000, None)

        actual_response = create_vertices_edges(inc_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_logs')
    def test_increment_delete(self, mock_logs, *patchs):
        """unit test for incremental delete"""

        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        patchs[2].return_value = '123'
        patchs[1].return_value = True
        patchs[0].return_value = [project_response()]
        patchs[3].side_effect = mock_response()
        patchs[4].side_effect = [get_response('scc_response.json', True)]
        # patchs[5].return_value = {'vm_instance': {'8466577108601329971'}}
        inc_import_obj.get_data_for_delta(1662009569000, None)

        # Mock Edge patch response
        patchs[7].return_value = {'status': 'success'}

        # Mock active edge response
        patchs[8].side_effect = [{'status': 'success'}, {'status': 'success'}]
        # Mock logs:
        mock_logs.side_effect = [get_response('vm_create_log.json', True)]
        inc_import_obj.projects = ["dummyproj"]
        assert inc_import_obj.delete_vertices() is None

    @patch('connector.server_access.AssetServer.get_resource_names_from_log')
    def test_incremental_web_applications_create(self, mock_resource, *patchs):
        """unit test for incremental create web app"""
        mock_resource.return_value = 'dummyapp'
        patchs[3].side_effect = [get_response('web_app.json', True),
                                 get_response('web_app_service.json', True),
                                 get_response('web_app_service_version.json', True)]
        patchs[9].return_value = get_response('schema.json', True)
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        app, service = inc_import_obj. incremental_web_applications('project')
        assert app is not None
        assert service is not None
