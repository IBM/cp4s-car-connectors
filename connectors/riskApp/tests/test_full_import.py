import unittest
from unittest.mock import patch, Mock

from tests import common_validate
from tests.common_validate import context, context_patch, TestConsumer, JsonResponse

class TestDRMFullImportFunctions(unittest.TestCase):

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_application(self, mock_get_total_records, mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetRetention"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint,param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_AssetRetention(item)
            validations = all([
                common_validate.TestConsumer.application_validate(collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_businessprocess(self, mock_get_total_records, mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'businessprocess.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetUsage"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint,param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_AssetUsage(item)
            validations = all([
                common_validate.TestConsumer.businessprocess_validate(collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_ipaddress(self, mock_get_total_records, mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'ipaddress_new.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetDSList"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint,param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_AssetDSList(item)
            validations = all([
                common_validate.TestConsumer.ip_adr_validate(collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_businessprocee_application(self, mock_get_total_records, mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'businessprocess_application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "ApplicationBPMapping"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint,param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_ApplicationBPMapping(item)
            validations = all([
                common_validate.TestConsumer.businessprocess_application_validate(collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_bearer_Token')
    @patch('connector.server_access.DRMServer.get_total_records')
    def test_ipaddress_application(self, mock_get_total_records, mock_get_bearer_Token):
        mock_get_total_records.return_value = JsonResponse(200, 'ipaddress_application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "DSAPPLICATION"
        param = context().args.last_model_state_id
        actual_response = context().drm_server.get_collection(drm_server_endpoint,param)
        assert actual_response is not None
        for item in actual_response:
            collection = context().data_handler.handle_DSAPPLICATION(item)
            if collection !={}:
                validations = all([common_validate.TestConsumer.ipaddress_application_validate(collection),])
            else:
                pass
        assert validations is True