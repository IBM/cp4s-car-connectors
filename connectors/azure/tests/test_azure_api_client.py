"""Unit Test Case For Azure Api Client"""
import unittest
from unittest.mock import patch

from tests.common_validate import context, context_patch, JsonResponse, MockJsonResponse, JsonTextResponse

ACCESS_TOKEN = 'xyz-abc-123'

@patch('connector.server_access.AssetServer.get_access_token')
@patch('connector.server_access.RestApiClient.call_api')
class TestAzureApiClient(unittest.TestCase):

    def test_administrative_logs(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for administrative logs.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_administrative.json')
        mock_log_details.return_value = mock_response
        map_data_administrative = context().asset_server.get_administrative_logs(context().last_model_state_id)
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    # def test_administrative_exception(self, mock_log_details, mock_access_token):
    #     """
    #         Summary: unit test for administrative log exceptions.
    #     """
    #     context_patch()
    #     response = """{
    #                    "error" : {
    #                        "code" : "SubscriptionNotFound",
    #                        "message":"The subscription could not be found"
    #                                }
    #                    }"""
    #     mock_access_token.return_value = ACCESS_TOKEN
    #     mock_log_details.return_value = MockJsonResponse(400, response)
    #     map_data_administrative = context().asset_server.get_administrative_logs(context().last_model_state_id)
        
    #     assert map_data_administrative.args[0].args[0]['success'] is False
    #     assert map_data_administrative.args[0].args[0]['status_code'] == 400


    def test_administrative_while_next(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for administrative log with while_next True.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_administrative.json')
        mock_while_response = JsonResponse(200, 'activity_log_next_data.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_administrative_logs(context().last_model_state_id)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_administrative_break(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for administrative log break statement.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_administrative.json')
        mock_while_response = JsonResponse(200, 'activity_log_break.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_administrative_logs(context().last_model_state_id)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_security_center_alerts(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for security center alerts.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_security_alerts.json')
        mock_log_details.return_value = mock_response
        map_data_administrative = context().asset_server.get_security_center_alerts(context().last_model_state_id)
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_security_alerts_while_next(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for security center alerts with while_next True.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_security_alerts.json')
        mock_while_response = JsonResponse(200, 'activity_log_next_data.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_security_center_alerts(context().last_model_state_id)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_security_alerts_break(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for security_alerts break statement.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_security_alerts.json')
        mock_while_response = JsonResponse(200, 'activity_log_break.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_security_center_alerts(context().last_model_state_id)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_security_logs(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for security logs.
         """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_security.json')
        mock_log_details.return_value = mock_response
        security_log_response = context().asset_server.get_security_logs(context().last_model_state_id)
        assert security_log_response['value'] is not None
        assert security_log_response['value'][0]['correlationId'] is not None
        assert security_log_response['value'][0]['eventTimestamp'] is not None
        assert security_log_response['value'][0]['id'] is not None
        assert mock_response.status_code == 200

    # @patch('azure.report_incremental.update_delete_nodes')
    # @patch('connector.server_access.AssetServer.get_administrative_logs')
    # def test_security_exception(self, mock_administrative_logs, mock_incremental_update, mock_log_details, mock_access_token):
    #     """
    #         Summary: unit test for security log exceptions.
    #     """
    #     context_patch()
    #     response = """{
    #         "error" : {
    #         "code": "GatewayTimeout", 
    #         "Message": "The gateway did not receive a response from Microsoft.Network within the specified time period."
    #                         }
    #         }"""
    #     mock_access_token.return_value = ACCESS_TOKEN
    #     mock_administrative_logs.return_value = None
    #     mock_incremental_update.return_value = None
    #     mock_log_details.return_value = MockJsonResponse(504, response)
    #     # context = TextContext(update=True)
    #     consumer = Consumer(context)
    #     map_data = report_initial_import.main(context, consumer)
    #     assert map_data.args[0].args[0]['success'] is False
    #     assert map_data.args[0].args[0]['status_code'] == 504

    def test_security_while_next(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for security log with while_next True.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_security.json')
        mock_while_response = JsonResponse(200, 'activity_log_next_data.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_security_logs(context().last_model_state_id)
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_security_break(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for security log break statement.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_security.json')
        mock_while_response = JsonResponse(200, 'activity_log_break.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_security_logs(context().last_model_state_id)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

#     def test_security_logs_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for administrative log exceptions.
#            """
#         context_patch()
#         response = """{
#                        "error" : {
#                            "code" : "SubscriptionNotFound",
#                            "message":"The subscription could not be found"
#                                    }
#                        }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_security_logs(context().last_model_state_id)
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

    def test_virtual_machine_details(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for virtual machine details.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'vm_details_testdata.json')
        mock_log_details.return_value = mock_response
        vm_details_response = context().asset_server.get_virtual_machine_details('/abc/xyz', True)
        assert vm_details_response['value'] is not None
        assert vm_details_response['value'][0]['type'] == 'Microsoft.Compute/virtualMachines'
        assert mock_response.status_code == 200

#     def test_vm_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for virtual machine details exception.
#            """
#         context_patch()
#         response = """{
#                        "error" : {
#                            "code" : "SubscriptionNotFound",
#                            "message":"The subscription could not be found"
#                                    }
#                        }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_virtual_machine_details('/abc/xyz', True)
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

    def test_vm_break(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for vm details for break statement.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'vm_details_testdata.json')
        mock_while_response = JsonResponse(200, 'activity_log_break.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_virtual_machine_details('/abc/xyz', False)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_virtual_machine_details_by_name(self, mock_log_details, mock_access_token):
        """
            Summary unit test for virtual machine details by name.
         """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'vm_details_testdata.json')
        mock_log_details.return_value = mock_response
        vm_details_response = context().asset_server.get_virtual_machine_details_by_name('test-abc-vm', 'xyz')
        assert vm_details_response['value'][0]['type'] == 'Microsoft.Compute/virtualMachines'
        assert vm_details_response['value'][0]['id'] == '/abc/xyz'
        assert mock_response.status_code == 200

#     def test_vm_by_name_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for virtual machine details by name exception case.
#            """
#         context_patch()
#         response = """{
#                        "error" : {
#                            "code" : "SubscriptionNotFound",
#                            "message":"The subscription could not be found"
#                                    }
#                        }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_virtual_machine_details_by_name('test-abc-vm', 'xyz')
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

    def test_virtual_machine_while_next(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for virtual machine log with while_next True.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'vm_details_testdata.json')
        mock_while_response = JsonResponse(200, 'activity_log_next_data.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_virtual_machine_details(context().last_model_state_id, True)
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

#     @patch('connector.server_access.AssetServer.get_security_logs')
#     def test_virtual_machine_exception(self, mock_security_logs, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for virtual machine exceptions.
#         """
#         context_patch()
#         response = """{
#            "error" : {
#            "code": "GatewayTimeout", 
#            "Message": "The gateway did not receive a response from Microsoft.Network within the specified time period."
#                            }
#                }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_security_logs.return_value = None
#         mock_log_details.return_value = MockJsonResponse(504, response)
#         # context = TextContext(update=True)
#         consumer = Consumer(context)
#         map_data = report_initial_import.main(context, consumer)
#         assert map_data.args[0].args[0]['success'] is False
#         assert map_data.args[0].args[0]['status_code'] == 504
#         assert map_data is not None

    def test_network_profile(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for network profile.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_network_details.json')
        mock_log_details.return_value = mock_response
        network_log_response = context().asset_server.get_network_profile('/ABC/123/XY-Z', True)
        assert network_log_response is not None
        assert network_log_response['value'][0]['name'] is not None
        assert network_log_response['value'][0]['type'] is not None
        assert network_log_response['value'][0]['properties']['ipConfigurations'] is not None
        assert mock_response.status_code == 200

    def test_network_while_next(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for network log with while_next True.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_network_details.json')
        mock_while_response = JsonResponse(200, 'activity_log_next_data.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_network_profile(context().last_model_state_id, True)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

#     def test_network_profile_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for network profile exception.
#         """
#         context_patch()
#         response = """{
#                               "error" : {
#                                   "code" : "SubscriptionNotFound",
#                                   "message":"The subscription could not be found"
#                                           }
#                               }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_network_profile(context().last_model_state_id, True)
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

    def test_network_profile_break(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for network profile break statement.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'vm_details_testdata.json')
        mock_while_response = JsonResponse(200, 'activity_log_break.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_network_profile(context().last_model_state_id, False)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

#     @patch('connector.server_access.AssetServer.get_virtual_machine_details')
#     @patch('connector.server_access.AssetServer.get_security_logs')
#     def test_network_exception(self, mock_security_logs, mock_vm_details, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for network exceptions.
#         """
#         context_patch()
#         response = """{
#                "error" : {
#                "code": "GatewayTimeout", 
#                "Message": "The gateway did not receive a response from Microsoft.Network within the specified time period."
#                                }
#                    }"""
#         mock_security_logs.return_value = None
#         mock_vm_details.return_value = None
#         mock_log_details.return_value = MockJsonResponse(504, response)
#         mock_access_token.return_value = ACCESS_TOKEN
#         # context = TextContext(update=True)
#         consumer = Consumer(context)
#         map_data = report_initial_import.main(context, consumer)
#         assert map_data is not None
#         assert map_data.args[0].args[0]['success'] is False
#         assert map_data.args[0].args[0]['status_code'] == 504

    def test_public_ip_address(self, mock_log_details, mock_access_token):
        """
            Summary unit test for public ip address.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_public_ip_address.json')
        mock_log_details.return_value = mock_response
        network_log_response = context().asset_server.get_public_ipaddress('/abc/public-ipaddress')
        assert network_log_response is not None
        assert mock_response.status_code == 200

#     def test_public_ip_address_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for public ip address exception.
#         """
#         context_patch()
#         response = """{
#                               "error" : {
#                                   "code" : "NoRegisteredProviderFound",
#                                   "message":"No registered resource provider found for location centralus." 
#                                           }
#                               }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_public_ipaddress('/abc/public-ipaddress')
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

    def test_application_details(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for application details.
         """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_application_details.json')
        mock_log_details.return_value = mock_response
        application_log_response = context().asset_server.get_application_details('/abc/application/sample_url', True)
        assert application_log_response is not None
        assert application_log_response['value'][0]['name'] is not None
        assert application_log_response['value'][0]['type'] is not None
        assert application_log_response['value'][0]['properties']['hostNames'] is not None
        assert mock_response.status_code == 200

#     def test_application_details_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for application details exception.
#         """
#         context_patch()
#         response = """{
#                               "error" : {
#                                   "code" : "SubscriptionNotFound",
#                                   "message":"The subscription could not be found"
#                                           }
#                               }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_application_details('/abc/application/sampleurl', True)
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

    def test_application_break(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for application details break statement.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_application_details.json')
        mock_while_response = JsonResponse(200, 'activity_log_break.json')
        mock_log_details.side_effect = [mock_response, mock_while_response]
        map_data_administrative = context().asset_server.get_application_details('/abc/application/sampleurl', False)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_application_details_by_name(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for application details by name.
         """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_application_details.json')
        mock_log_details.return_value = mock_response
        application_log_response = context().asset_server.get_application_details_by_name('carjavaapp', 'test_group')
        assert application_log_response is not None
        assert application_log_response['value'][0]['name'] == 'carjavaapp'
        assert application_log_response['value'][0]['type'] == 'Microsoft.Web/sites'
        assert application_log_response['value'][0]['properties']['hostNames'] is not None
        assert mock_response.status_code == 200

#     def test_app_details_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for application details exception.
#         """
#         context_patch()
#         response = """{
#                           "error" : {
#                               "code" : "SubscriptionNotFound",
#                               "message":"The subscription could not be found"
#                                       }
#                               }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_application_details_by_name('carjavaapp', 'test_group')
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

    def test_application_while_next(self, mock_log_details, mock_access_token):
        """
            Summary: unit test for application with while_next True.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_application_details.json')
        mock_while_response = JsonResponse(200, 'activity_log_next_data.json')
        mock_log_details.side_effect = [mock_while_response, mock_response]
        map_data_administrative = context().asset_server.get_application_details(context().last_model_state_id, True)
        assert map_data_administrative is not None
        assert map_data_administrative['value'] is not None
        assert mock_response.status_code == 200

    def test_database_details(self, mock_log_details, mock_access_token):
        """
            Summary unit test for database_details.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'Sql_server_details.json')
        mock_log_details.return_value = mock_response
        database_log_response = context().asset_server.get_sql_database_details('/abc/01dfc-xyz/sample-db')
        assert database_log_response is not None
        assert database_log_response['name'] is not None
        assert database_log_response['type'] == 'Microsoft.DBforMySQL/servers/databases'
        assert mock_response.status_code == 200

#     def test_sql_database_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for database_details exception.
#         """
#         context_patch()
#         response = """{
#                    "error" : {
#                        "code" : "MissingSubscription",
#                        "message": "The request did not have a subscription or a valid tenant level resource provider."
#                                }
#                         }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_sql_database_details('/abc/01dfc-xyz/sample-db')
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

    def test_database_details_by_name(self, mock_log_details, mock_access_token):
        """
            Summary unit test for database_details by name.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_database_details.json')
        mock_log_details.return_value = mock_response
        db_log_response = context().asset_server.get_sql_database_details_by_name('sample_db', 'test-server', 'test-group')
        assert db_log_response is not None
        assert db_log_response['value'][0]['name'] is not None
        assert db_log_response['value'][0]['type'] == 'Microsoft.Sql/servers/databases'
        assert mock_response.status_code == 200

#     def test_sql_db_by_name_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for database_details exception by name.
#         """
#         context_patch()
#         response = """{
#             "error" : {
#                 "code" : "GatewayTimeout",
#                 "message":"The gateway did not receive a response from Microsoft.Network within the specified time period"
#             }
#                 }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(504, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_sql_database_details_by_name('sample_db', 'test-server', 'test-group')
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 504
#         assert the_exception.args[0].args[0]['success'] == False

    def test_all_sql_database_details(self, mock_log_details, mock_access_token):
        """
            Summary unit test for sql_database_details.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_sql_databases.json')
        mock_log_details.return_value = mock_response
        database_log_response = context().asset_server.get_all_sql_databases()
        assert database_log_response is not None
        assert database_log_response['value'][0]['name'] is not None
        assert database_log_response['value'][0]['type'] == 'Microsoft.Sql/servers/databases'
        assert mock_response.status_code == 200

#     def test_all_sql_db_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for sql_database_details exception.
#         """
#         context_patch()
#         response = """{
#                            "error" : {
#                                "code" : "SubscriptionNotFound",
#                                "message":"The subscription could not be found"
#                                        }
#                            }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_all_sql_databases()
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0].args[0]['success'] == False

    def test_sql_server_details(self, mock_log_details, mock_access_token):
        """
            Summary unit test for sql_server_details.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'activity_log_server_details.json')
        mock_log_details.return_value = mock_response
        database_log_response = context().asset_server.get_sql_servers('test_group')
        assert database_log_response is not None
        assert database_log_response['value'][0]['name'] == 'mysqlservercar'
        assert database_log_response['value'][0]['type'] == 'Microsoft.Sql/servers'
        assert mock_response.status_code == 200

#     def test_sql_server_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for sql server exception.
#         """
#         context_patch()
#         response = """{
#                           "error" : {
#                               "code" : "SubscriptionNotFound",
#                               "message":"The subscription could not be found"
#                                       }
#                           }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(400, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_sql_servers('test_group')
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 400
#         assert the_exception.args[0].args[0]['success'] == False

#     def test_sql_by_name_exception(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for sql by name exception.
#         """
#         context_patch()
#         response = """{
#           "error" : {
#               "code" : "GatewayTimeout",
#               "message":"The gateway did not receive a response from Microsoft.Network within the specified time period"
#                 }
#                     }"""
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = MockJsonResponse(504, response)
#         # context = TextContext(update=True)
#         with self.assertRaises(Exception) as cm:
#             context().asset_server.get_sql_server_by_name("group", "sql_server")
#         the_exception = cm.exception
#         assert the_exception.args[0].args[0]['status_code'] == 504
#         assert the_exception.args[0].args[0]['success'] == False

    # def test_handle_json_errors(self, mock_log_details, mock_access_token):
    #     """
    #         Summary: unit test for handle errors exception case.
    #     """
    #     context_patch()
    #     response = """{
    #                     "error" : {
    #                      "code" : "SubscriptionNotFound",
    #                      "message": "The subscription 083de1fb-cd2d-4b7c-895-2b5af1d091e8 could not be found"
    #                              }
    #                     }"""
    #     mock_access_token.return_value = ACCESS_TOKEN
    #     mock_log_details.return_value = None
    #     with self.assertRaises(Exception) as cm:
    #         AzureApiClient.handle_errors(JsonTextResponse(404, response), {})
    #     the_exception = cm.exception
    #     assert the_exception.args[0]['success'] is False
    #     assert the_exception.args[0]['status_code'] == 404
    #     assert the_exception is not None

#     def test_handle_string_error(self, mock_log_details, mock_access_token):
#         """
#             Summary: unit test for handle errors error scenario.
#         """
#         context_patch()
#         response = """
#                      "error" : {
#                          "code" : "NoRegisteredProviderFound",
#                          "message": "No registered resource provider found for location"
#                                  }
#                 """
#         context_patch()
#         mock_access_token.return_value = ACCESS_TOKEN
#         mock_log_details.return_value = None
#         with self.assertRaises(Exception) as cm:
#             AzureApiClient.handle_errors(MockJsonResponse(400, response), {})
#         the_exception = cm.exception
#         assert the_exception.args[0]['success'] is False
#         assert the_exception.args[0]['error_type'] == "unknown"
#         assert the_exception is not None


class TestAccessToken(unittest.TestCase):

    @patch('adal.authentication_context.AuthenticationContext.acquire_token_with_client_credentials')
    def test_generate_access_token(self, access_token):
        """
            Summary: token generation with good return.
        """
        context_patch()
        access_token.return_value = {'accessToken': 'ACCESS_TOKEN'}
        # context = TextContext(update=True)
        access_token_response = context().asset_server.get_access_token()
        assert access_token_response is not None
        assert isinstance(access_token_response, str)

    # @patch('connector.server_access.RestApiClient.call_api')
    # def test_generate_access_token_error(self, mock_log_details):
    #     """
    #         Summary: token generation with error return.
    #     """
    #     context_patch()
    #     mock_response = JsonResponse(200, 'activity_log_administrative.json')
    #     mock_log_details.return_value = mock_response
    #     # context = TextContext(update=True)
    #     consumer = Consumer(context)
    #     map_data = report_initial_import.main(context, consumer)
    #     assert map_data.args[0].args[0]['success'] is False


