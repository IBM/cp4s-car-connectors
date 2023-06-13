import json
import unittest
from unittest.mock import patch
from connector import data_handler
from tests.test_utils import inc_import_initialization, \
    get_response, TaniumMockResponse, create_vertices_edges, validate_all_handler, JsonResponse


class TestIncImportFunctions(unittest.TestCase):
    @patch('connector.server_access.AssetServer.execute_query')
    @patch('car_framework.car_service.CarService.get_import_schema')
    def test_import_collection(self, schema, mock_detections_list):
        """
             unit test for importing collections.
        """
        mock_response = get_response('tanium_node_resp.json', True)
        mock_detections_list.return_value.text = json.dumps(mock_response)

        schema.return_value = JsonResponse(200, 'schema.json').json()

        inc_import_obj = inc_import_initialization()
        inc_import_obj.last_model_state_id = data_handler.get_report_time()
        inc_import_obj.create_source_report_object()
        inc_import_obj.get_data_for_delta(data_handler.get_report_time(), None)
        inc_import_obj.import_collection()

        actual_response = create_vertices_edges(inc_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None


