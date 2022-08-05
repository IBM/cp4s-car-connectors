import unittest
from unittest.mock import patch
from tests.test_utils import inc_import_initialization, create_vertices_edges, \
    get_response, validate_all_handler, mocking_apis


class TestIncrementalImportFunctions(unittest.TestCase):
    """Unit test for incremental import"""

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_create(self, mock_api):
        """Test Incremental create"""
        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        mock_api.side_effect = mocking_apis()

        inc_import_obj.get_data_for_delta(1651375759000, None)

        # Initiate incremental create
        actual_response = create_vertices_edges(inc_import_obj)

        # validate the response
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_update(self, mock_api):
        """Test Incremental update"""
        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        mock_api.side_effect = mocking_apis()

        inc_import_obj.get_data_for_delta(1651375759000, None)

        # Initiate incremental create update
        actual_response = create_vertices_edges(inc_import_obj)

        # validate the response
        validations = validate_all_handler(actual_response)

        assert validations is True
        assert actual_response is not None

    @patch('car_framework.car_service.CarService.search_collection')
    @patch('car_framework.car_service.CarService.edge_patch')
    @patch('car_framework.car_service.CarService.delete')
    @patch('connector.server_access.AssetServer.get_collection')
    def test_incremental_delete(self, mock_api, mock_car_delete, mock_patch, mock_collection):
        """Test Incremental delete"""
        # Initialization
        inc_import_obj = inc_import_initialization()
        inc_import_obj.create_source_report_object()

        # Mocking API's
        mock_response = mocking_apis()
        mock_cve_obj = get_response('cve.json', True)
        mock_images_obj = get_response('images.json', True)
        mock_response.extend([mock_cve_obj, mock_images_obj])
        mock_api.side_effect = mock_response

        inc_import_obj.get_data_for_delta(1649396087, None)

        # Mock Edge patch response
        mock_patch.return_value = {'status': 'success'}

        mock_assets = {'asset': [{'external_id': '1fc674e36f58659948a51fb43d42eee7f2a91831cbb9da58f2e4d3873804113e',
                       'asset_type': 'container'}, {'external_id': 'a9bb4695-8335-473b-beea-8dc4fd44c6ba',
                                                    'asset_type': 'cluster'}]}
        mock_ipaddress = {'ipaddress': [{'external_id': '0/172.22.22.22'}]}

        mock_user = {'user': [{'external_id': 'Danial'}]}

        mock_collection.side_effect = [mock_assets, mock_ipaddress, mock_user]

        # Mock active edge response
        mock_car_delete.return_value = {'status': 'success'}

        inc_import_obj.delete_vertices()

        assert inc_import_obj.delete_vertices is not None
