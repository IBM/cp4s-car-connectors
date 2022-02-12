import unittest
from connector import data_handler
from unittest.mock import patch, Mock
from tests.test_utils import full_import_initialization, create_vertices_edges, get_response, validate_all_handler


class TestInitialImportFunctions(unittest.TestCase):

    """Unit test for full import"""

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import(self, mock_api):
        """Unit test for import vertices"""

        # Initialization
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()

        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.json')
        res_application_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=200)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_application_detail

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_header, mock_application_detail]

        # Initiate full import
        actual_response = create_vertices_edges(full_import_obj)
        # validate the response
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_full_import_without_vul_detail(self, mock_api):
        """Unit test for import vertices
        doesn't have a vulnerability details"""

        # Initialization
        full_import = full_import_initialization()
        full_import.create_source_report_object()

        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset.json', True)
        res_vulnerability_detail = get_response('no_vulnerability_detail.json')
        res_app_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=200)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_app_detail

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_header, mock_application_detail]

        # Initiate full import
        actual_response = create_vertices_edges(full_import)

        assert 'vulnerability' not in actual_response
        assert actual_response is not None

    def test_get_new_model_state_id(self):
        """unitest for model_state_id"""
        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        date_id = full_import_obj.get_new_model_state_id()
        assert date_id is not None

    def test_get_report_time(self):
        """Convert current ut time to epoch time"""
        milli_sec = data_handler.get_report_time()
        assert isinstance(milli_sec, float)
