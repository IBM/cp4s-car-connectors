import unittest
from unittest.mock import patch, Mock
from tests import common_validate
from tests.common_validate import context, context_patch, TestConsumer, JsonResponse


class TestDRMIncrementalImportFunctions(unittest.TestCase):

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_application_incremental(self,mock_get_total_records,mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'update_application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetRetention"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for obj in actual_response:
           collection= context().data_handler.handle_AssetRetention(obj)
           validations = all([
                common_validate.TestConsumer.update_application_validate(self,collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_businessprocess_incremental(self, mock_get_total_records,mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'update_businessprocess.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetUsage"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for obj in actual_response:
            collection = context().data_handler.handle_AssetUsage(obj)
            validations = all([
                common_validate.TestConsumer.update_businessprocess_validate(self,collection),

        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_ipaddress_incremental(self, mock_get_total_records,mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'update_ipaddress.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetDSList"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for obj in actual_response:
            collection = context().data_handler.handle_AssetDSList(obj)
            validations = all([
                common_validate.TestConsumer.update_ipaddress_validate(self,collection),
        ])
        assert validations is True


    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_businessprocee_application(self, mock_get_total_records,mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'businessprocess_application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "ApplicationBPMapping"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_ApplicationBPMapping(item)
            validations = all([
                common_validate.TestConsumer.businessprocess_application_validate(collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_ipaddress_application(self, mock_get_total_records,mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'ipaddress_application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "DSAPPLICATION"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_DSAPPLICATION(item)
            if collection != {}:
                validations = all([
                    common_validate.TestConsumer.ipaddress_application_validate(collection),
        ])
        assert validations is True


    @patch('car_framework.base_import.BaseImport.send_data')
    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_create_edge_ipaddress_application(self, mock_get_total_records, mock_get_bearer_Token, mock_send_data):
        mock_get_total_records.side_effect = [JsonResponse(200, 'update_application.json').json()['data'],
                                           JsonResponse(200, 'ipaddress_application.json').json()['data'],
                                           JsonResponse(200, 'update_application.json').json()['data'],
                                           JsonResponse(200, 'businessprocess_application.json').json()['data']]
        context_patch()
        drm_server_endpoint = "AssetRetention"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for obj in actual_response:
            new_edge_collection = context().drm_server.get_collection(drm_server_endpoint, param)
            for item in new_edge_collection:
                if item['parentConceptId'] == str(obj['id']) or item['childConceptId'] == str(obj['id']):
                    collection = context().data_handler.handle_DSAPPLICATION(item)
                    validations = all([
                                    common_validate.TestConsumer.ipaddress_application_validate(collection),
                                        ])
                    assert validations is True
        actual_response = context().drm_server.get_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for obj in actual_response:
            new_edge_collection = context().drm_server.get_collection(drm_server_endpoint, param)
            for item in new_edge_collection:
                if item['parentId'] == str(obj['id']) or item['childConcept']['id'] == str(obj['id']):
                    collection = context().data_handler.handle_ApplicationBPMapping(item)
                    validations = all([
                        common_validate.TestConsumer.businessprocess_application_validate(collection),
                    ])
                    assert validations is True


    @patch('car_framework.base_import.BaseImport.send_data')
    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_create_edge_businessprocess_application(self, mock_get_total_records, mock_get_bearer_Token, mock_send_data):
        mock_get_total_records.side_effect = [JsonResponse(200, 'update_businessprocess.json').json()['data'],
                                           JsonResponse(200, 'businessprocess_application.json').json()['data'],
                                           JsonResponse(200, 'update_businessprocess.json').json()['data'],
                                           JsonResponse(200, 'businessprocess_application.json').json()['data']]
        context_patch()
        drm_server_endpoint = "AssetUsage"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for obj in actual_response:
            drm_server_endpoint = "ApplicationBPMapping"
            new_edge_collection = context().drm_server.get_collection(drm_server_endpoint, param)
            for item in new_edge_collection:
                if item['parentId'] == str(obj['id']) or item['childConcept']['id'] == str(obj['id']):
                    collection = context().data_handler.handle_ApplicationBPMapping(item)
                    validations = all([
                        common_validate.TestConsumer.businessprocess_application_validate(collection),
                    ])
                    assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_delete_application(self, mock_get_total_records, mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'deleted_application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetRetention"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_deleted_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_AssetRetention(item)
        validations = all([
            common_validate.TestConsumer.deleted_application_validate(self,collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_delete_ipaddress(self, mock_get_total_records, mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'deleted_ipaddress.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetRetention"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_deleted_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_AssetDSList(item)
        validations = all([
            common_validate.TestConsumer.deleted_ipaddress_validate(self, collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_delete_businessprocess(self, mock_get_total_records, mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'deleted_businessprocess.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetRetention"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_deleted_collection(drm_server_endpoint, param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_AssetUsage(item)
        validations = all([
            common_validate.TestConsumer.deleted_businessprocess_validate(self, collection),
        ])
        assert validations is True











