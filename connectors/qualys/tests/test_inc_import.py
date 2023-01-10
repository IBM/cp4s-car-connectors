import unittest
from connector import data_handler
from unittest.mock import patch, Mock
from tests.test_utils import create_vertices_edges, get_response, inc_import_initialization, validate_all_handler


class TestIncImportFunctions(unittest.TestCase):
    """unittest for incremental run"""

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create_update(self, mock_api):
        """Unit test for import collection"""

        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.xml')
        inc_import_obj.last_model_state_id = data_handler.get_report_time()
        res_application_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_application_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)

        # Initiate incremental create and update
        actual_response = create_vertices_edges(inc_import_obj)

        # validate the response
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_inc_import_without_vul_detail(self, mock_api):
        """Unit test for import vertices
        doesn't have a vulnerability details"""

        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        # mock host asset, vulnerability, application api
        res_host_asset = get_response('host_asset.json', True)
        res_vulnerability_detail = get_response('no_vulnerability_detail.xml')
        res_application_detail = get_response('application_detail.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_application_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)

        # Initiate incremental create and update
        actual_response = create_vertices_edges(inc_import_obj)

        assert 'vulnerability' not in actual_response
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.edge_patch')
    @patch('connector.inc_import.IncrementalImport.get_active_asset_edges')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_delete_vertices(self, mock_api, mock_active_edges, mock_patch):
        """Unit test for import vertices
        doesn't have a vulnerability details"""

        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        # mock host asset, vulnerability, application and car graph search api
        res_host_asset = get_response('host_asset.json', True)
        res_vulnerability_detail = get_response('vulnerability_detail.xml')
        res_application_detail = get_response('application_detail.json', True)
        res_active_edges = get_response('asset_active_edges.json', True)

        mock_host_asset = Mock(status_code=200)
        mock_host_asset.json.return_value = res_host_asset

        mock_vulnerability_detail = Mock(status_code=200)
        mock_vulnerability_detail.text = res_vulnerability_detail

        mock_header = Mock(status_code=201)
        mock_header.text = 'abcd'

        mock_application_detail = Mock(status_code=200)
        mock_application_detail.json.return_value = res_application_detail

        # Mock vulnerability kb details for detections
        vuln_kb = get_response('vulnerability_kb_details.xml')
        mock_kb = Mock(status_code=200)
        mock_kb.text = vuln_kb

        mock_api.side_effect = [mock_host_asset, mock_vulnerability_detail, mock_kb, mock_header, mock_application_detail]
        active_edge = {}
        for key, value in res_active_edges.items():
            active_edge[key] = set(value)
        mock_active_edges.return_value = active_edge
        mock_patch.return_value = {'status': 'success'}

        # Initiate delete vertices process
        inc_import_obj.get_data_for_delta('1663784167208.183', None)

        inc_import_obj.delete_vertices()

        assert len(inc_import_obj.update_edge) != 0

    def test_get_new_model_state_id(self):
        """unitest for model_state_id"""
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        date_id = inc_import_obj.get_new_model_state_id()
        assert date_id is not None
