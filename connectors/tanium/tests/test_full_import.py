import json
import unittest
from unittest.mock import patch
from tests.test_utils import full_import_initialization, \
    get_response, TaniumMockResponse, create_vertices_edges, validate_all_handler, JsonResponse


class TestImportFull(unittest.TestCase):
    @patch('connector.server_access.AssetServer.execute_query')
    @patch('car_framework.car_service.CarService.get_import_schema')
    def test_import_collection(self, schema, mock_node_data):
        """
             unit test for importing collections.
        """

        mock_response = get_response('tanium_node_resp.json', True)
        mock_node_data.return_value.text = json.dumps(mock_response)

        schema.return_value = JsonResponse(200, 'schema.json').json()

        full_import_obj = full_import_initialization()
        full_import_obj.create_source_report_object()
        full_import_obj.import_collection()

        actual_response = create_vertices_edges(full_import_obj)
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None


