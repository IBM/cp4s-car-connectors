import unittest
from unittest.mock import patch

from tests.common_validate import context, context_patch, JsonResponse, MockJsonResponse, TestConsumer


ACCESS_TOKEN = 'xyz-abc-123'


class TestImportIncremental(unittest.TestCase):

    @patch('connector.server_access.AssetServer.get_machine_list')
    def test_create_asset_host_update(self, mock_machine_list):
        """
             Summary unit test for create asset host for update.
        """
        context_patch()
        mock_machine_list.return_value = JsonResponse(200, 'vm_details_log.json').json()
        actual_response = context().data_collector.create_asset_host(incremental=True)
        assert actual_response is not None
        context().inc_importer.handle_data([
            'asset',
            'hostname',
            'asset_hostname',
            'application',
            'asset_application',
        ], actual_response)

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
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
    @patch('connector.server_access.AssetServer.get_user_information')
    def test_create_ip_mac_update(self, mock_user_detail, mock_private_ip_response, mock_machine_list):
        """
             Summary unit test for create ip address mac address update.
        """
        context_patch()
        mock_machine_list.return_value = JsonResponse(200, 'vm_details_log.json').json()
        mock_private_ip_response.return_value = JsonResponse(200, 'private_ip_log.json').json()
        mock_user_detail.return_value = JsonResponse(200, 'user_details_log.json').json()
        
        network_list, ip_data, mac_data, ip_mac = context().data_collector.create_ipaddress_macaddress(incremental=True) 
        assert network_list is not None
        assert ip_data is not None
        assert mac_data is not None
        assert ip_mac is not None
        
        context().inc_importer.handle_data([
            'asset',
            'hostname',
            'asset_hostname',
            'application',
            'asset_application',
            'ipaddress',
            'macaddress',
            'ipaddress_macaddress',
            'asset_ipaddress',
            'asset_macaddress',
        ], network_list)
    
        context().inc_importer.handle_data([
            'ipaddress',
            'asset_ipaddress',
        ], ip_data)
    
        context().inc_importer.handle_data([
            'macaddress',
            'asset_macaddress',
        ], mac_data)
    
        context().inc_importer.handle_data([
            'ipaddress_macaddress',
        ], ip_mac)

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
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

    @patch('connector.server_access.AssetServer.get_machine_list')
    @patch('connector.server_access.AssetServer.vulnerability_information')
    @patch('connector.server_access.AssetServer.get_alerts_list')
    @patch('car_framework.communicator.Communicator.get')
    def test_create_vulnerability_update(self, mock_log_details, mock_alert_log, mock_vuln_vm_details, mock_machine_list):
        """
             Summary unit test for create vulnerability update.
        """
        context_patch()
        mock_machine_list.return_value = JsonResponse(200, 'vm_details_log.json').json()
        mock_vuln_vm_details.return_value = JsonResponse(200, 'machine_vuln_details.json').json()
        mock_alert_log.return_value = JsonResponse(200, 'alerts_log.json').json()
        mock_log_details.return_value = JsonResponse(200, 'graph_search_log.json')
        vuln_list, application_create, vulnerability_update, app_vuln_edge, vulnerability_create = context().data_collector.create_vulnerability(incremental=True)
        assert vuln_list is not None
        assert application_create is not None
        assert vulnerability_update is not None
        assert app_vuln_edge is not None
        assert vulnerability_create is not None

        context().inc_importer.handle_data([
            'application',
            'asset_application',
            'vulnerability',
            'asset_vulnerability',
            'application_vulnerability'
        ], vuln_list)

        context().inc_importer.handle_data([
            'application',
            'asset_application',
            'application_vulnerability'
        ], application_create)
        
        context().inc_importer.handle_data([
            'vulnerability',
            'asset_vulnerability',
            'application_vulnerability'
        ], vulnerability_update)
        
        context().inc_importer.handle_data([
            'application_vulnerability'
        ], app_vuln_edge)
            
        context().inc_importer.handle_data([
            'application',
            'asset_application',
            'application_vulnerability',
            'vulnerability',
            'asset_vulnerability',
        ], vulnerability_create)

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.application_validate(collections.get('application')),
            validate.asset_application_validate(edges.get('asset_application')),
            validate.vuln_validate(collections.get('vulnerability')),
            validate.asset_vuln_validate(edges.get('asset_vulnerability')),
            validate.application_vulnerability_validate(edges.get('application_vulnerability'))
        ])
        assert validations is True


    @patch('connector.server_access.AssetServer.get_access_token')
    @patch('connector.server_access.RestApiClient.call_api')
    @patch('connector.server_access.AssetServer.get_machine_list')
    def test_create_user_update(self, mock_machine_list, mock_user_details, mock_access_token):
        """
             Summary unit test for create user update.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_machine_list.return_value = JsonResponse(200, 'vm_details_log.json').json()
        mock_user_details.return_value = JsonResponse(200, 'user_details_log.json')
        actual_response = context().data_collector.create_user(incremental=False)
        assert actual_response is not None
        context().inc_importer.handle_data([
            'user',
            'asset_account',
            'account_hostname',
            'account',
            'user_account',
        ], actual_response)

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.user_validate(collections.get('user')),
            validate.asset_account_validate(edges.get('asset_account')),
            validate.account_host_validate(edges.get('account_hostname')),
            validate.account_validate(collections.get('account')),
            validate.user_account_validate(edges.get('user_account')),
        ])
        assert validations is True

    @patch('connector.server_access.AssetServer.get_access_token')
    @patch('connector.server_access.RestApiClient.call_api')
    @patch('car_framework.car_service.CarService.delete')
    def test_delete_asset(self, mocked_send_delete, mock_log_details, mock_access_token):
        """
             Summary unit test for delete asset.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_response = JsonResponse(200, 'vm_details_log.json')
        mock_log_details.return_value = mock_response
        actual_response = context().data_collector.delete_vertices()
        assert actual_response is not None

        is_valid_asset = []
        for item in actual_response:
            assert item is not None
            is_valid_id = isinstance(item, str)
            is_valid_asset.append(is_valid_id)
            
        assert all(is_valid_asset)
        assert len(actual_response) == 9

    @patch('connector.server_access.AssetServer.get_access_token')
    @patch('car_framework.communicator.Communicator.get')
    @patch('connector.server_access.AssetServer.get_user_information')
    def test_updates_network_address(self, mock_user_details, mock_log_details, mock_access_token):
        """
             Summary unit test for ip mac address incremental update asset.
        """
        context_patch()
        mock_access_token.return_value = ACCESS_TOKEN
        mock_log_details.return_value = JsonResponse(200, 'graph_search_log.json')
        mock_user_details.return_value = JsonResponse(200, 'user_details_log.json').json()
        ip_mac, mac_data, mac_list = [], [], []
        ntwrk_data = JsonResponse(200, 'network_data.json').json()
        context().data_collector.updates_network_address(ntwrk_data['network_update'], ip_mac, mac_data, mac_list)
        
        assert ip_mac is not None and len(ip_mac) == 3
        assert mac_data is not None and len(mac_data) == 1
        assert mac_list is not None and len(mac_list) == 3

    # def test_asset_user_update(self):
    #     """
    #          Summary unit test for asset user update.
    #     """
    #     context_patch()
    #     actual_response = context().data_collector.asset_account_update(context,'M-123',['Sampleuser'])
    #     assert actual_response is None

    # @patch('connector.server_access.AssetServer.get_alerts_list')
    # def test_alerts_update(self,mock_alerts_log):
    #     """
    #          Summary unit test for alerts update.
    #     """
    #     context_patch()
    #     mock_alerts_log.return_value = JsonResponse(200, 'alerts_log.json').json()
    #     actual_response = context().data_collector.alerts_update(context, [])
    #     assert actual_response is None


