import unittest
from unittest.mock import patch

from tests.common_validate import context, context_patch, JsonResponse, TestConsumer

ACCESS_TOKEN = 'xyz-abc-123'


class TestImportFull(unittest.TestCase):

    @patch('connector.server_access.AssetServer.get_machine_list')
    @patch('car_framework.car_service.CarService.get_import_schema')
    def test_create_asset_host(self, schema, mock_machine_list):
        """
             Summary unit test for create asset host.
        """
        context_patch(incremental=False)
        mock_machine_list.return_value = JsonResponse(200, 'vm_details_log.json').json()
        schema.return_value = JsonResponse(200, 'schema.json').json()
        actual_response = context().data_collector.create_asset_host(incremental=False)
        assert actual_response is not None
        context().full_importer.handle_data([
            'asset',
            'hostname',
            'asset_hostname',
            'application',
            'asset_application',
        ], actual_response)

        collections = context().full_importer.data_handler.collections
        edges = context().full_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.asset_validate(collections.get('asset')),
            validate.host_validate(collections.get('hostname')), 
            validate.asset_host_validate(edges.get('asset_hostname')),
            validate.application_validate(collections.get('application')),
            validate.asset_application_validate(edges.get('asset_application'))
        ])
        assert validations is True


    @patch('connector.server_access.AssetServer.get_machine_list')
    @patch('connector.server_access.AssetServer.mac_private_ip_information')
    @patch('car_framework.car_service.CarService.get_import_schema')
    def test_create_ip_mac(self, schema, mock_private_ip_response, mock_machine_list):
        """
             Summary unit test for create ipaddress macaddress.
        """
        context_patch(incremental=False)
        mock_machine_list.return_value = JsonResponse(200, 'vm_details_log.json').json()
        mock_private_ip_response.return_value = JsonResponse(200, 'private_ip_log.json').json()
        schema.return_value = JsonResponse(200, 'schema.json').json()
        actual_response, _, _, _ = context().data_collector.create_ipaddress_macaddress(incremental=False)
        assert actual_response is not None
        context().full_importer.handle_data([
            'ipaddress',
            'macaddress',
            'ipaddress_macaddress',
            'asset_ipaddress',
            'asset_macaddress',
            'asset',
            'hostname',
            'asset_hostname',
            'application',
            'asset_application',
        ], actual_response)

        collections = context().full_importer.data_handler.collections
        edges = context().full_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.ipaddr_validate(collections.get('ipaddress')),
            validate.mac_validate(collections.get('macaddress')),
            validate.ip_mac_address_validate(edges.get('ipaddress_macaddress')),
            validate.asset_ip_validate(edges.get('asset_ipaddress')),
            validate.asset_mac_validate(edges.get('asset_macaddress')),
            validate.asset_validate(collections.get('asset')),
            validate.host_validate(collections.get('hostname')),
            validate.asset_host_validate(edges.get('asset_hostname')),
            validate.application_validate(collections.get('application')),
            validate.asset_application_validate(edges.get('asset_application'))
        ])
        assert validations is True


    @patch('connector.server_access.AssetServer.vulnerability_information')
    @patch('connector.server_access.AssetServer.get_alerts_list')
    @patch('connector.server_access.AssetServer.get_machine_list')
    @patch('car_framework.car_service.CarService.get_import_schema')
    def test_create_vulnerability(self, schema, mock_machine_list, mock_alert_log, mock_vuln_vm_details):
        """
             Summary unit test for create vulnerability.
        """
        context_patch(incremental=False)
        # test_log_data = JsonResponse(200, 'vulnerability_log.json')
        mock_machine_list.return_value = JsonResponse(200, 'vm_details_log.json').json()
        mock_alert_log.return_value = JsonResponse(200, 'alerts_log.json').json()
        mock_vuln_vm_details.return_value = JsonResponse(200, 'machine_vuln_details.json').json()
        schema.return_value = JsonResponse(200, 'schema.json').json()
        actual_response, _, _, _, _ = context().data_collector.create_vulnerability(incremental=False)
  
        assert actual_response is not None
        context().full_importer.handle_data([
            'application',
            'asset_application',
            'vulnerability',
            'asset_vulnerability'
        ], actual_response)

        collections = context().full_importer.data_handler.collections
        edges = context().full_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.application_validate(collections.get('application')),
            validate.asset_application_validate(edges.get('asset_application')),
            validate.vuln_validate(collections.get('vulnerability')),
            validate.asset_vuln_validate(edges.get('asset_vulnerability'))
        ])
        assert validations is True


    @patch('connector.server_access.AssetServer.get_access_token')
    @patch('connector.server_access.RestApiClient.call_api')
    @patch('connector.server_access.AssetServer.get_machine_list')
    @patch('car_framework.car_service.CarService.get_import_schema')
    def test_create_user(self, schema, mock_machine_list, mock_user_details, mock_access_token):
        """
             Summary unit test for create user.
        """
        context_patch(incremental=False)
        mock_access_token.return_value = ACCESS_TOKEN
        mock_machine_list.return_value = JsonResponse(200, 'vm_details_log.json').json()
        schema.return_value = JsonResponse(200, 'schema.json').json()
        mock_user_details.return_value = JsonResponse(200, 'user_details_log.json')
        actual_response = context().data_collector.create_user(incremental=False)
        assert actual_response is not None
        context().full_importer.handle_data([
            'user',
            'asset_account',
            'account_hostname',
            'account',
            'user_account',
        ], actual_response)

        collections = context().full_importer.data_handler.collections
        edges = context().full_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.user_validate(collections.get('user')),
            validate.asset_account_validate(edges.get('asset_account')),
            validate.account_host_validate(edges.get('account_hostname')),
            validate.account_validate(collections.get('account')),
            validate.user_account_validate(edges.get('user_account')),
        ])
        assert validations is True

