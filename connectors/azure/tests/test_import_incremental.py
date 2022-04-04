import unittest
from unittest.mock import patch

from tests.common_validate import context_patch, context, JsonResponse, TestConsumer

@unittest.skip("Incremental import skipping")
class TestImportIncremental(unittest.TestCase):

    @patch('connector.server_access.AssetServer.get_administrative_logs')
    @patch('connector.server_access.AssetServer.get_network_profile')
    @patch('connector.server_access.AssetServer.get_public_ipaddress')
    @patch('car_framework.communicator.Communicator.get')
    def test_create_ipaddress_macaddress_update(self, mock_graph_details, mock_public_ipaddress, mock_get_network_profile, mock_administrative_logs):
        """
         Summary unit test for create ipAddress macAddress with update True.
        """
        context_patch()

        mock_administrative_logs.return_value = JsonResponse(200, 'activity_log_administrative.json').json()
        mock_get_network_profile.return_value = JsonResponse(200, 'network_details.json').json()
        mock_public_ipaddress.return_value = JsonResponse(200, 'activity_log_public_ip_address.json').json()
        mock_graph_details.return_value = JsonResponse(200, 'graph_search_log.json')

        context().inc_importer.create_ipaddress_macaddress()

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()
        
        validations = all([
            validate.ip_adr_validate(collections.get('ipaddress')),
            validate.edges_validate(edges.get('ipaddress_macaddress')),
            validate.edges_validate(edges.get('asset_ipaddress')),
        ])
        assert validations is True

    
    @patch('connector.server_access.AssetServer.get_administrative_logs')
    @patch('connector.server_access.AssetServer.get_virtual_machine_details')
    @patch('car_framework.communicator.Communicator.get')
    def test_create_asset_host_update(self, mock_graph_details, mock_vm_detail, mock_administrative_logs):
        """
        Summary unit test for test_create_asset_host_update with update/delete True.
        """
        context_patch()
        mock_vm_detail.return_value = JsonResponse(200, 'vm_details.json').json()
        mock_administrative_logs.return_value = JsonResponse(200, 'activity_log_administrative.json').json()
        mock_graph_details.return_value = JsonResponse(200, 'graph_search_log.json')

        context().inc_importer.create_asset_host()

        collections = context().inc_importer.data_handler.collections
        validate = TestConsumer()
        
        validations = all([
            validate.asset_validate(collections.get('asset')),
        ])
        assert validations is True

    @patch('connector.server_access.AssetServer.get_administrative_logs')
    @patch('connector.server_access.AssetServer.get_application_details')
    @patch('car_framework.communicator.Communicator.get')
    def test_create_application_update(self, mock_graph_details, mock_app_detail, mock_administrative_logs):
        """
        Summary unit test for create_application with update True.
        """
        context_patch()
        mock_app_detail.return_value = JsonResponse(200, 'application_details.json').json()
        mock_administrative_logs.return_value = JsonResponse(200, 'activity_log_administrative.json').json()
        mock_graph_details.return_value = JsonResponse(200, 'graph_search_log.json')

        context().inc_importer.create_application()

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()
        
        validations = all([
            validate.ip_adr_validate(collections.get('ipaddress')),
            validate.edges_validate(edges.get('asset_ipaddress')),
        # TODO: we need to test also the collections below, but we don't have data yet
        #     validate.asset_validate(collections.get('asset')),
        #     validate.host_validate(collections.get('hostname')),
        #     validate.application_validate(collections.get('application')),
        #     validate.edges_validate(edges.get('asset_application')),
        #     validate.edges_validate(edges.get('asset_hostname')),
        ])
        assert validations is True


    @patch('connector.server_access.AssetServer.get_administrative_logs')
    @patch('connector.server_access.AssetServer.get_sql_database_details')
    @patch('car_framework.communicator.Communicator.get')
    def test_create_database_update(self, mock_graph_details, mock_db_detail, mock_administrative_logs):
        """
         Summary unit test for create_database with update True.
        """
        context_patch()
        sql_db_data = JsonResponse(200, 'database_map_log.json').json()
        mock_db_detail.return_value = sql_db_data['database_map']
        mock_administrative_logs.return_value = JsonResponse(200, 'activity_log_administrative.json').json()
        mock_graph_details.return_value = JsonResponse(200, 'graph_search_log_null.json')

        context().inc_importer.create_database()

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()
        
        validations = all([
            validate.db_validate(collections.get('database')),
            validate.asset_validate(collections.get('asset')),
            validate.host_validate(collections.get('hostname')),
            validate.edges_validate(edges.get('asset_database')),
            validate.edges_validate(edges.get('asset_hostname')),
        ])
        assert validations is True
     
    @patch('connector.server_access.AssetServer.get_administrative_logs')
    @patch('connector.server_access.AssetServer.get_public_ipaddress')
    @patch('connector.server_access.AssetServer.get_network_profile')
    @patch('car_framework.communicator.Communicator.get')
    def test_update_host_name(self, mock_graph_details, mock_ntwrk_details, mock_host_details, mock_administrative_logs):
        """
               Summary unit test for update host name.
         """
        context_patch()
        mock_administrative_logs.return_value = JsonResponse(200, 'activity_log_administrative.json').json()
        mock_host_details.return_value = JsonResponse(200, 'activity_log_public_ip_address.json').json()
        mock_ntwrk_details.return_value = JsonResponse(200, 'network_details.json').json()
        mock_graph_details.return_value = JsonResponse(200, 'graph_search_log.json')

        context().inc_importer.update_hostname_vm()

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.host_validate(collections.get('hostname')),
            validate.edges_validate(edges.get('asset_hostname')),
        ])
        assert validations is True


    @patch('connector.server_access.AssetServer.get_administrative_logs')
    @patch('connector.server_access.AssetServer.get_application_details')
    @patch('car_framework.communicator.Communicator.get')
    def test_update_host_app(self,  mock_graph_details, mock_host_details, mock_administrative_logs):
        """
               Summary unit test for update host name.
         """
        context_patch()
        mock_administrative_logs.return_value = JsonResponse(200, 'activity_log_administrative.json').json()
        mock_host_details.return_value = JsonResponse(200, 'application_details.json').json()
        mock_graph_details.return_value = JsonResponse(200, 'graph_search_log.json')

        context().inc_importer.update_hostname_app()

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.host_validate(collections.get('hostname')),
            validate.edges_validate(edges.get('asset_hostname')),
        ])
        assert validations is True


    def test_update_delete_nodes(self):
        """unit test for report incremental administrative logs filter based on operation types."""
        context_patch()
        test_data = JsonResponse(200, "activity_log_administrative.json")
        actual_response = context().data_collector.update_delete_nodes(test_data.json())
        assert 'vm', 'application' in actual_response
        assert 'database', 'container' in actual_response
        assert 'network' in actual_response
        assert actual_response is not None

    def test_update_delete_nodes_vm(self):
        """
        unit test for report incremental for delete vm
            """
        context_patch()
        test_data = JsonResponse(200, "activity_log_vm_admin.json")
        actual_response = context().data_collector.update_delete_nodes(test_data.json())
        assert 'vm', 'application' in actual_response
        assert 'database', 'container' in actual_response
        assert 'network' in actual_response
        assert actual_response is not None

    def test_update_delete_nodes_web(self):
        """
        unit test for report incremental for delete web
            """
        context_patch()
        test_data = JsonResponse(200, "activity_log_web_admin.json")
        actual_response = context().data_collector.update_delete_nodes(test_data.json())
        assert 'vm', 'application' in actual_response
        assert 'database', 'container' in actual_response
        assert 'network' in actual_response
        assert actual_response is not None

    def test_update_delete_nodes_db(self):
        """
        unit test for report incremental for delete db
            """
        context_patch()
        test_data = JsonResponse(200, "activity_log_db_admin.json")
        actual_response = context().data_collector.update_delete_nodes(test_data.json())
        assert 'vm', 'application' in actual_response
        assert 'database', 'container' in actual_response
        assert 'network' in actual_response
        assert actual_response is not None

    def test_update_delete_nodes_ntwrk(self):
        """
        unit test for report incremental for delete network
            """
        context_patch()
        test_data = JsonResponse(200, "activity_log_ntwrk_admin.json")
        actual_response = context().data_collector.update_delete_nodes(test_data.json())
        assert 'vm', 'application' in actual_response
        assert 'database', 'container' in actual_response
        assert 'network' in actual_response
        assert actual_response is not None

    @patch('car_framework.communicator.Communicator.get')
    def test_update_ipaddress_both(self, mock_graph_log):
        """unit test for both ip address update."""
        context_patch()
        update_network, network_list = [], []
        test_data = JsonResponse(200, "ip_address_log.json")
        mock_graph_log.return_value = JsonResponse(200, 'graph_search_log.json')
        context().data_collector.updates_ipaddress(test_data.json(), update_network, network_list)

        assert update_network[0]["network_map"]["properties"]["ipConfigurations"]["properties"]["IPAddress"] is not None
        assert len(network_list) == 0

    @patch('car_framework.communicator.Communicator.get')
    def test_update_ipaddress_public(self, mock_graph_log):
        """unit test for public ip address update."""
        context_patch()
        update_network, network_list = [], []
        test_data = JsonResponse(200, "ip_address_log.json")
        mock_graph_log.return_value = JsonResponse(200, 'graph_search_log_1.json')
        context().data_collector.updates_ipaddress(test_data.json(), update_network, network_list)

        assert update_network[0]["network_map"]["properties"]["ipConfigurations"]["properties"]["IPAddress"] is not None
        assert len(network_list) == 0
        

    @patch('car_framework.communicator.Communicator.get')
    def test_update_ipaddress_private(self, mock_graph_log):
        """unit test for private ip address."""
        context_patch()
        update_network, network_list = [], []
        test_data = JsonResponse(200, "ip_address_log.json")
        mock_graph_log.return_value = JsonResponse(200, 'graph_search_log_2.json')
        context().data_collector.updates_ipaddress(test_data.json(), update_network, network_list)
        
        assert update_network[0]["network_map"]["properties"]["ipConfigurations"]["properties"]["IPAddress"] is not None
        assert len(network_list) == 0

    @patch('car_framework.communicator.Communicator.get')
    def test_update_ipaddress_nwcreate(self, mock_graph_log):
        """unit test for network ip address create."""
        context_patch()
        update_network, network_list = [], []
        test_data = JsonResponse(200, "ip_address_log.json")
        mock_graph_log.return_value = JsonResponse(200, 'graph_search_log_null.json')
        context().data_collector.updates_ipaddress(test_data.json(), update_network, network_list)
        
        assert len(update_network) == 0
        assert network_list[0]["network_map"]["properties"]["ipConfigurations"]["properties"]["IPAddress"] is not None

    @patch('car_framework.communicator.Communicator.get')
    def test_update_ipaddress_appcreate(self, mock_graph_log):
        """unit test for application ip address create."""
        context_patch()
        update_network, network_list = [], []
        test_data = JsonResponse(200, "application_log.json")
        mock_graph_log.return_value = JsonResponse(200, 'graph_search_log_null.json')
        context().data_collector.updates_ipaddress(test_data.json(), update_network, network_list)
        
        assert len(update_network) == 0
        assert network_list[0]["application_map"]["properties"]["inboundIpAddress"] is not None

    @patch('car_framework.communicator.Communicator.get')
    def test_updates_hostname(self, mock_graph_log):
        context_patch()
        """unit test for host name."""
        update_list, host_list = [], []
        test_data = JsonResponse(200, "application_log.json")
        mock_graph_log.return_value = JsonResponse(200, 'graph_search_log.json')
        context().data_collector.updates_hostname(test_data.json(), update_list, host_list)

        assert update_list[0]["application_map"]["properties"]["hostNames"] == ['dummytestapp.azurewebsites.net']
        assert len(host_list) == 0

    
    @patch('car_framework.communicator.Communicator.get')
    def test_updates_hostname_create(self, mock_graph_log):
        """unit test for host name create."""
        context_patch()
        update_list, host_list = [], []
        test_data = JsonResponse(200, "application_log.json")
        mock_graph_log.return_value = JsonResponse(200, 'graph_search_log_null.json')
        context().data_collector.updates_hostname(test_data.json(), update_list, host_list)

        assert len(update_list) == 0
        assert host_list[0]["application_map"]["properties"]["hostNames"] == ['dummytestapp.azurewebsites.net']

