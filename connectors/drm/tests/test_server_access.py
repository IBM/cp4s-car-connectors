import unittest
from unittest.mock import patch
from tests import common_validate
from tests.common_validate import context, context_patch, JsonResponse

class TestAwsApiClient(unittest.TestCase):

    @patch('connector.server_access.DRMServer.get_total_records')
    @patch('connector.server_access.DRMServer.get_bearer_Token')
    def test_get_collection( self,mock_get_bearer_Token, mock_get_total_records):
        mock_get_total_records.return_value = JsonResponse(200, 'application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint="AssetRetention"
        param=context().args.last_model_state_id
        collection =context().drm_server.get_collection(drm_server_endpoint, param)
        assert collection is not None
        validations = all([
                common_validate.TestConsumer.get_collection_validate(collection),
        ])
        assert validations is True

    @patch('connector.server_access.DRMServer.get_total_records')
    @patch('connector.server_access.DRMServer.get_bearer_Token')
    def test_get_deleted_collection(self, mock_get_bearer_Token, mock_get_total_records):
        mock_get_total_records.return_value = JsonResponse(200, 'deleted_application.json').json()['data']
        mock_get_bearer_Token.return_value = JsonResponse(200, 'access_token.json').json()['data']
        context_patch()
        drm_server_endpoint = "AssetRetention"
        param = context().args.last_model_state_id
        collection = context().drm_server.get_deleted_collection(drm_server_endpoint, param)
        assert collection is not None
        validations = all([
            common_validate.TestConsumer.get_deleted_collection_validate(self,collection),
        ])
        assert validations is True


