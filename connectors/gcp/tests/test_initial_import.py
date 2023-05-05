import unittest
from unittest.mock import patch

from tests.test_utils import full_import_initialization, \
    create_vertices_edges, validate_all_handler, \
    get_response, project_response, mock_response


class TestInitialImportFunctions(unittest.TestCase):
    """Unit test for full import"""

    @patch('googleapiclient.discovery.build')
    @patch('connector.server_access.AssetServer.get_logs')
    @patch('car_framework.car_service.CarService.get_import_schema')
    @patch('connector.server_access.AssetServer.get_vulnerabilities')
    @patch('connector.server_access.AssetServer.get_asset_list')
    @patch('google.oauth2.service_account.Credentials.from_service_account_info')
    @patch('google.cloud.resourcemanager_v3.SearchProjectsRequest')
    @patch('google.cloud.resourcemanager_v3.ProjectsClient.search_projects')
    def test_import_collection(self, mock_search_project, mock_search_request, mock_credentials,
                               mock_asset_list, mock_vulnerability, mock_schema, mock_log, mock_discovery):
        """unit test for import collection"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        mock_credentials.return_value = '123'
        mock_search_request.return_value = True
        mock_search_project.return_value = [project_response()]
        mock_asset_list.side_effect = mock_response()
        mock_vulnerability.side_effect = [get_response('scc_response.json', True)]
        mock_schema.return_value = get_response('schema.json', True)
        mock_log.return_value = get_response('gke_workload_vulns.json', True)
        mock_discovery.return_value.databases.return_value.list.return_value.execute.return_value = \
            get_response('sql_db.json', True)
        mock_discovery.return_value.users.return_value.list.return_value.execute.return_value = \
            get_response('sql_user.json', True)

        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    def test_get_new_model_state_id(self):
        """unitest for model_state_id"""

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        date_id = full_import_obj.get_new_model_state_id()
        assert date_id is not None
