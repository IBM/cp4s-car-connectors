"""Unit Test Case For MSATP Api Client"""
import json
import unittest
from unittest.mock import patch

from tests.common_validate import context, context_patch, JsonResponse, MockJsonResponse, JsonTextResponse


ACCESS_TOKEN = 'xyz-abc-123'


@patch('connector.server_access.AssetServer.get_access_token')
@patch('connector.server_access.RestApiClient.call_api')
class TestMsatpApiClient(unittest.TestCase):

    def test_get_machines_list(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for get machines list.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'vm_details_log.json')
        mock_log_details.return_value = mock_response
        actual_response = context().asset_server.get_machine_list(context().last_model_state_id)
        assert actual_response['value'] is not None
        assert mock_response.status_code == 200

    def test_get_machines_list_exception(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for get machines list exception.
        """
        context_patch()
        response = """{
                       "error" : {
                           "code" : "SubscriptionNotFound",
                           "message":"The subscription could not be found"
                                   }
                       }"""
        mock_access_token.return_value = ACCESS_TOKEN
        mock_log_details.return_value = MockJsonResponse(404, response)
        # context = TextContext(update=True)
        with self.assertRaises(Exception) as cm:
            context().asset_server.get_machine_list()
        except_obj = cm.exception.argsEEE[0]
        assert except_obj['status_code'] == 404
        assert except_obj['success'] is False

    def test_get_alerts_list(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for get alerts list.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'alerts_log.json')
        mock_log_details.return_value = mock_response
        actual_response = context().asset_server.get_alerts_list(True)
        assert actual_response['value'] is not None
        assert mock_response.status_code == 200

    def test_get_alerts_list_exception(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for get alerts list exception.
        """
        context_patch()
        response = """{
                       "error" : {
                           "code" : "SubscriptionNotFound",
                           "message":"The subscription could not be found"
                                   }
                       }"""
        mock_access_token.return_value = ACCESS_TOKEN
        mock_log_details.return_value = MockJsonResponse(400, response)
        # context = TextContext(update=True)
        with self.assertRaises(Exception) as cm:
            context().asset_server.get_alerts_list()
        except_obj = cm.exception.args[0]
        assert except_obj['status_code'] == 400
        assert except_obj['success'] is False

    def test_mac_private_ip_information(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for mac private ip information.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'private_ip_log.json')
        mock_log_details.return_value = mock_response
        # context = TextContext(update=False)
        machine_id = '7594a7860caaf0bdb5a3b68c341773bf004e3e14'
        actual_response = context().asset_server.mac_private_ip_information(context, machine_id)
        assert actual_response['Results'] is not None
        assert mock_response.status_code == 200

    def test_mac_private_ip_information_update(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for mac private ip information.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'private_ip_log.json')
        mock_log_details.return_value = mock_response
        # context = TextContext(update=True)
        machine_id = '7594a7860caaf0bdb5a3b68c341773bf004e3e14'
        actual_response = context().asset_server.mac_private_ip_information(context, machine_id)
        assert actual_response['Results'] is not None
        assert mock_response.status_code == 200

    def test_mac_private_ip_exception(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for mac private ip exception.
        """
        context_patch()
        response = """{
                       "error" : {
                           "code" : "GatewayTimeout",
                           "message":"The gateway did not receive a response from Microsoft\
                           Network within the specified time period."
                                   }
                       }"""
        mock_access_token.return_value = ACCESS_TOKEN
        mock_log_details.return_value = MockJsonResponse(504, response)
        # context = TextContext(update=True)
        with self.assertRaises(Exception) as cm:
            context().asset_server.mac_private_ip_information(context, None)
        except_obj = cm.exception.args[0]
        assert except_obj['status_code'] == 504
        assert except_obj['success'] is False


    def test_get_user_information(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for get user information.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'user_details_log.json')
        mock_log_details.return_value = mock_response
        # context = TextContext(update=True)
        actual_response = context().asset_server.get_user_information('7594a7860caaf0bdb5a3b68c341773bf004e3e14')
        assert actual_response['value'] is not None
        assert mock_response.status_code == 200

    def test_get_user_info_exception(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for get user exception.
        """
        context_patch()
        response = """{
                       "error" : {
                           "code" : "SubscriptionNotFound",
                           "message":"The subscription could not be found"
                                   }
                       }"""
        mock_access_token.return_value = ACCESS_TOKEN
        mock_log_details.return_value = MockJsonResponse(404, response)
        # context = TextContext(update=True)
        with self.assertRaises(Exception) as cm:
            context().asset_server.get_user_information(None)
        except_obj = cm.exception.args[0]
        assert except_obj['status_code'] == 404
        assert except_obj['success'] is False

    def test_handle_json_errors(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for handle errors exception case.
        """
        context_patch()
        response = """{
                        "error" : {
                         "code" : "SubscriptionNotFound",
                         "message": "The subscription 083de1fb-cd2d-4b7c-895-2b5af1d091e8 could not be found"
                                 }
                        }"""
        mock_access_token.return_value = ACCESS_TOKEN
        mock_log_details.return_value = None
        with self.assertRaises(Exception) as cm:
            context().asset_server.handle_errors(JsonTextResponse(404, response), {})
        the_exception = cm.exception
        assert the_exception.args[0]['success'] is False
        assert the_exception.args[0]['status_code'] == 404
        assert the_exception is not None

    def test_handle_string_error(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for handle errors error scenario.
        """
        context_patch()
        response = """
                     "error" : {
                         "code" : "NoRegisteredProviderFound",
                         "message": "No registered resource provider found for location"
                                 }
                        """
        mock_access_token.return_value = ACCESS_TOKEN
        mock_log_details.return_value = None
        with self.assertRaises(Exception) as cm:
            context().asset_server.handle_errors(MockJsonResponse(400, response), {})
        the_exception = cm.exception
        assert the_exception.args[0]['success'] is False
        assert the_exception.args[0]['error_type'] == "unknown"
        assert the_exception is not None

    def test_vuln_info(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for vulnerability info.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'vulnerability_log.json')
        mock_log_details.return_value = mock_response
        # context = TextContext(update=True)
        actual_response = context().asset_server.vulnerability_information('7594a7860caaf0bdb5a3b68c341773bf004e3e14')
        assert actual_response['value'] is not None
        assert mock_response.status_code == 200

    def test_vuln_info_exception(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for vulnerability info exception.
        """
        context_patch()
        response = """{
                         "error" : {
                             "code" : "SubscriptionNotFound",
                             "message":"The subscription could not be found"
                                     }
                         }"""
        mock_access_token.return_value = ACCESS_TOKEN
        mock_log_details.return_value = MockJsonResponse(404, response)

        with self.assertRaises(Exception) as cm:
            context().asset_server.vulnerability_information('7594a7860caaf0bdb5a3b68c341773bf004e3e14')
        except_obj = cm.exception.args[0]
        assert except_obj['status_code'] == 404
        assert except_obj['success'] is False


class TestAccessToken(unittest.TestCase):

    @patch('adal.authentication_context.AuthenticationContext.acquire_token_with_client_credentials')
    def test_generate_access_token(self, access_token):
        """
            Summary: token generation with good return.
        """
        context_patch()
        access_token.return_value = {'accessToken': 'ACCESS_TOKEN'}
        access_token_response = context().asset_server.get_access_token()
        assert access_token_response is not None
        assert isinstance(access_token_response, str)

    @patch('adal.authentication_context.AuthenticationContext.acquire_token_with_client_credentials')
    def test_generate_access_token_error(self, access_token):
        """
            Summary: token generation with bad return.
        """
        context_patch()
        access_token.return_value = {'accessTokenb': 'ACCESS_TOKEN'}
        with self.assertRaises(Exception) as cm:
            context().asset_server.get_access_token()
        the_exception = cm.exception
        assert the_exception.args[0]['success'] is False

