import unittest
from connector import data_handler
from unittest.mock import patch
from tests.test_utils import inc_import_initialization, create_vertices_edges, \
    get_response, validate_all_handler, OktaMockResponse


class TestIncrementalImportFunctions(unittest.TestCase):
    """Unit test for full import"""

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create(self, mock_api, active_edges):
        """Test Incremental create"""
        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
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
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)

        # Mock active edge response
        active_edges.return_value = []
        # Initiate incremental create and update
        actual_response = create_vertices_edges(inc_import_obj)

        # validate the response
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_update(self, mock_api, active_edges):
        """Test Incremental update"""
        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        # mock users, app, application users, event logs api
        inc_create_collections = get_response('inc_update_collections.json', True)

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
                                mock_events, mock_user,
                                mock_events_disable]
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)

        # Mock active edge response
        active_edges.return_value = []
        # Initiate incremental create and update
        actual_response = create_vertices_edges(inc_import_obj)

        # validate the response
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.edge_patch')
    @patch('car_framework.car_service.CarService.search_collection')
    @patch('car_framework.car_service.CarService.delete')
    @patch('connector.server_access.AssetServer.get_systemlogs')
    @patch('connector.server_access.AssetServer.get_asset_collections')
    def test_incremental_delete(self, mock_api, mock_events, mock_car_delete, active_edges, mock_edge):
        """Test Incremental delete"""
        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()
        mock_car_delete.return_value = {'status': 'success'}
        mock_edge.return_value = {'status': 'success'}
        delta = {'user': [], 'application': [], 'client': []}
        mock_api.return_value = delta

        # user and application delete event log
        inc_delete_collections = get_response('inc_delete_collections.json', True)
        mock_events.side_effect = [inc_delete_collections['user'], inc_delete_collections['user'],
                                   inc_delete_collections['application']]
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)

        # Mock active edge response
        mock_active_edges = get_response('active_edges_mock_res.json', True)
        active_edges.side_effect = mock_active_edges

        assert inc_import_obj.delete_vertices() is None

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_get_new_model_state_id(self, mock_auth, active_edges):
        """unitest for model_state_id"""
        mock_auth.return_value = {'status_code': 200}
        full_import_obj = inc_import_initialization()
        full_import_obj.create_source_report_object()
        # Mock active edge response
        active_edges.return_value = []
        date_id = full_import_obj.get_new_model_state_id()
        assert date_id is not None
