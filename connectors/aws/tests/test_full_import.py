import unittest
import json
from unittest.mock import patch, Mock

from tests.common_validate import context, context_patch, TestConsumer, JsonResponse


class TestAwsFullImportFunctions(unittest.TestCase):

    @patch('connector.server_access.AssetServer.get_instances')
    @patch('connector.server_access.AssetServer.get_image_name')
    @patch('connector.server_access.AssetServer.list_applications')
    @patch('connector.server_access.AssetServer.list_applications_env')
    def test_create_asset(self, mock_env_details, mock_app_details, mock_image_details, mock_get_instances):
        """Unit test for create asset"""
        result_list = list()
        test_log_data = JsonResponse(200, 'Instance_details.json').json()
        mock_env_details.return_value = JsonResponse(200, 'environment_log.json').json()
        mock_image_details.return_value = "TestImage"
        mock_get_instances.return_value = JsonResponse(200, 'get_instance.json').json()
        context_patch()

        result_list.extend(test_log_data['Reservations'])
        actual_response = context().data_collector.create_asset(incremental=False)
        
        assert actual_response is not None
        context().inc_importer.handle_data([
            'asset',
            'application',
            'asset_application',
            'ipaddress', 
            'hostname',
            'macaddress',
            'ipaddress_macaddress',
            'asset_ipaddress',
            'asset_hostname',
            'asset_macaddress',
            'geolocation',
            'asset_geolocation',
        ], actual_response)

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.asset_validate(collections.get('asset')),
            validate.application_validate(collections.get('application')),
            validate.ip_adr_validate(collections.get('ipaddress')),
            validate.host_validate(collections.get('hostname')), 
            validate.mac_validate(collections.get('macaddress')),
            validate.geolocation_validate(collections.get('geolocation')),
            validate.edges_validate(edges.get('asset_application')),
            validate.edges_validate(edges.get('ipaddress_macaddress')),
            validate.edges_validate(edges.get('asset_ipaddress')),
            validate.edges_validate(edges.get('asset_hostname')),
            validate.edges_validate(edges.get('asset_macaddress')),
            validate.edges_validate(edges.get('asset_geolocation'))
        ])
        assert validations is True

    @patch('connector.data_collector.DataCollector.update_private_ipv4')
    @patch('connector.server_access.AssetServer.get_instances')
    @patch('car_framework.car_service.CarService.graph_search', return_value=Mock())
    @patch('car_framework.car_service.CarService.graph_attribute_search', return_value=Mock())
    @patch('connector.server_access.AssetServer.get_network_interface')
    @patch('connector.server_access.AssetServer.event_logs', return_value=Mock())
    def test_create_network(self, mock_event_details, mock_ntwrk_details, mock_attr_details,
                                 mock_graph_details, mock_instance_details, mock_ip_details):
        """Unit test for network_incremental"""
        detach_ntwrk_log = JsonResponse(200, 'detach_ntwrk_log.json').json()
        attach_ntwrk_log = JsonResponse(200, 'attach_ntwrk_log.json').json()
        start_inst_log = JsonResponse(200, 'start_instance.json').json()
        for item in detach_ntwrk_log:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in attach_ntwrk_log:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in start_inst_log:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        mock_event_details.side_effect = [detach_ntwrk_log, attach_ntwrk_log, start_inst_log]
        mock_ntwrk_details.return_value = JsonResponse(200, 'ntwrk_interface_log.json').json()
        mock_instance_details.return_value = JsonResponse(200, 'get_instance.json').json()
        mock_ip_details.return_value = None
        graph_attr_search = [{'key': 'key-123', 'source': ['AWS-TEST']}]
        mock_attr_details.side_effect = [graph_attr_search, graph_attr_search, graph_attr_search]
        graph_search_log = JsonResponse(200, 'graph_search_log.json').json()
        mock_graph_details.side_effect = [graph_search_log, graph_search_log, graph_search_log, graph_search_log]
        context_patch()

        actual_response1, actual_response2 = context().data_collector.create_network()
        
        assert actual_response1 is not None
        assert actual_response2 is not None

        context().inc_importer.handle_data([
            'ipaddress',
            'hostname',
            'macaddress',
            'ipaddress_macaddress',
            'asset_ipaddress',
            'asset_hostname',
            'asset_macaddress',
        ], actual_response1)

        context().inc_importer.handle_data([
            'ipaddress',
            'hostname',
            'ipaddress_macaddress',
            'asset_ipaddress',
            'asset_hostname',
        ], actual_response2)
        
        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.ip_adr_validate(collections.get('ipaddress')), 
            validate.mac_validate(collections.get('macaddress')),
            validate.host_validate(collections.get('hostname')), 
            validate.edges_validate(edges.get('ipaddress_macaddress')),
            validate.edges_validate(edges.get('asset_ipaddress')),
            validate.edges_validate(edges.get('asset_hostname')),
            validate.edges_validate(edges.get('asset_macaddress'))
        ])

        assert validations is True

    @patch('connector.server_access.AssetServer.get_instances')
    @patch('connector.server_access.AssetServer.security_alerts')
    def test_create_vulnerability(self, mock_alerts_response, mock_get_instances):
        """Unit test for create vulnerability"""
        mock_alerts_response.return_value = JsonResponse(200, 'alerts_log.json').json()['Findings']
        mock_get_instances.return_value = JsonResponse(200, 'get_instance.json').json()

        context_patch()

        actual_response = context().data_collector.create_vulnerability(incremental=False)
        assert actual_response is not None
        
        context().inc_importer.handle_data([
            'vulnerability',
            'asset_vulnerability',
        ], actual_response)
        
        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.vuln_validate(collections.get('vulnerability')), 
            validate.edges_validate(edges.get('asset_vulnerability')),
        ])
        
        assert validations is True

    @patch('connector.server_access.AssetServer.list_applications')
    def test_create_application(self, mock_list_applications):
        """Unit test for create application."""
        mock_list_applications.return_value = JsonResponse(200, 'application_log.json').json()['Applications']
        
        context_patch()
        
        actual_response, _ = context().data_collector.create_application(incremental=False)
        assert actual_response is not None
        
        context().inc_importer.handle_data([
            'application'
        ], actual_response)
        
        collections = context().inc_importer.data_handler.collections
        validate = TestConsumer()

        validations = all([
            validate.application_validate(collections.get('application')),
        ])
        assert validations is True
        

    @patch('car_framework.car_service.CarService.graph_search')
    @patch('car_framework.car_service.CarService.graph_attribute_search')
    @patch('connector.server_access.AssetServer.get_db_instances')
    @patch('connector.server_access.AssetServer.get_db_instances')
    @patch('connector.server_access.AssetServer.event_logs')
    def test_create_database(self, mock_cloudtrail_events, mock_db_data, search_data, attribute_search, db_graph_data):
        """Unit test case for create RDS database"""
        mock_cloudtrail_events.return_value = JsonResponse(200, 'db_cloutrail_events.json').json()
        for item in mock_cloudtrail_events.return_value:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        mock_db_data.return_value = JsonResponse(200, 'db_list_log.json').json()
        search_data.return_value = JsonResponse(200, 'db_search.json').json()
        db_graph_data.return_value = JsonResponse(200, 'db_car_search.json').json()
        attribute_search.return_value = [{'external_id': ['AWS-TEST:db-GQNFWUQIV7BLAFOMGEDTPTN67M'], 'source':['AWS-TEST']}]
        context_patch()
        
        collection_create, _ = context().data_collector.create_database(incremental=False)
        assert collection_create is not None

        context().inc_importer.handle_data([
            'database',
            'asset_database',
            'asset',
            'hostname',
            'asset_hostname',
            'asset_geolocation',
            'geolocation',
            'account',
            'account_database',
            'application',
            'user',
            'user_account',
            'asset_application',
        ], collection_create)
        
        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.db_validate(collections.get('database')),
            validate.asset_validate(collections.get('asset')),
            validate.host_validate(collections.get('hostname')),
            validate.geolocation_validate(collections.get('geolocation')),
            validate.account_validate(collections.get('account')),
            validate.application_validate(collections.get('application')),
            validate.user_validate(collections.get('user')),
            validate.edges_validate(edges.get('asset_database')),
            validate.edges_validate(edges.get('asset_hostname')),
            validate.edges_validate(edges.get('asset_geolocation')),
            validate.edges_validate(edges.get('account_database')),
            validate.edges_validate(edges.get('user_account')),
            validate.edges_validate(edges.get('asset_application')),
        ])

        assert validations is True

    @patch('connector.server_access.AssetServer.list_running_containers')
    @patch('connector.server_access.AssetServer.get_instances')
    @patch('connector.server_access.AssetServer.container_ec2_instance')
    def test_create_container(self, mock_container_instances, mock_get_instances, mock_container_details):
        """Unit test cases for create container"""
        container_details = JsonResponse(200, 'container.json').json()['tasks']
        container_instances = JsonResponse(200, 'describe_container_instances.json').json()
        get_instances = JsonResponse(200, 'get_instance.json').json()
        mock_container_instances.return_value = container_instances
        mock_get_instances.return_value = get_instances
        mock_container_details.return_value = container_details
        context_patch()

        response = context().data_collector.create_container(incremental=False)

        assert response is not None

        context().inc_importer.handle_data([
            'container',
            'ipaddress',
            'asset_container',
            'ipaddress_container',
        ], response)
        
        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.container_validate(collections.get('container')),
            validate.edges_validate(edges.get('asset_container')),
            validate.edges_validate(edges.get('ipaddress_container')),
        ])

        assert validations is True
