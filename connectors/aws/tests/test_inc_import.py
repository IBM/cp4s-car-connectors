import unittest
import json
from unittest.mock import patch, Mock

from tests.common_validate import context, context_patch, TestConsumer, JsonResponse

class TestAwsIncImportFunctions(unittest.TestCase):

    @patch('connector.server_access.AssetServer.get_image_name')
    @patch('connector.server_access.AssetServer.list_applications')
    @patch('connector.server_access.AssetServer.list_applications_env')
    @patch('connector.server_access.AssetServer.event_logs', return_value=Mock())
    @patch('botocore.client.BaseClient._make_api_call')
    def test_create_asset_update(self,  mock_instance_details, mock_event_details, mock_env_details, mock_app_details,
                                 mock_image_details):
        """Unit test for create asset for update"""
        terminate_instances = JsonResponse(200, 'terminate_instance.json').json()
        run_instances = JsonResponse(200, 'run_instances.json').json()
        tags_log = JsonResponse(200, 'create_tags_log.json').json()
        for item in terminate_instances:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in run_instances:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in tags_log:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        mock_event_details.side_effect = [terminate_instances, run_instances, tags_log]
        mock_instance_details.return_value = JsonResponse(200, 'Instance_details.json').json()
        mock_env_details.return_value = JsonResponse(200, 'environment_log.json').json()
        mock_app_details.return_value = JsonResponse(200, 'application_log.json').json()["Applications"]
        mock_image_details.return_value = "TestImage"
        context_patch()

        actual_response = context().data_collector.create_asset(incremental=True)

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

    @patch('connector.server_access.AssetServer.list_applications')
    @patch('car_framework.car_service.CarService.graph_search')
    @patch('car_framework.car_service.CarService.graph_attribute_search', return_value=Mock())
    @patch('connector.server_access.AssetServer.list_applications_env')
    @patch('connector.server_access.AssetServer.event_logs', return_value=Mock())
    def test_create_application_update(self, mock_app_details, mock_env_details, mock_attr_details, mock_graph_details,
                                       mock_application):
        """Unit test for create application with update"""
        mock_application.return_value = JsonResponse(200, 'application_log.json').json()
        mock_env_details.return_value = JsonResponse(200, 'environment_log.json').json()
        mock_graph_details.return_value = JsonResponse(200, 'graph_search_log.json').json()
        app_del_data = JsonResponse(200, 'app_create_log.json').json()
        for item in app_del_data:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        app_create_data = JsonResponse(200, 'app_del_log.json').json()
        for item in app_create_data:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        swap_env_log = JsonResponse(200, 'swap_env_log.json').json()
        for item in swap_env_log:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        mock_app_details.side_effect = [app_del_data, app_create_data, swap_env_log]
        graph_attr_search = [{'external_id': ['AWS-TEST:id-123'], 'source':['AWS-TEST']}]
        mock_attr_details.side_effect = [graph_attr_search, graph_attr_search]
        context_patch()
        
        _, actual_response = context().data_collector.create_application(incremental=True)
        
        assert actual_response is not None
        
        context().inc_importer.handle_data([
            'hostname',
            'asset_hostname',
        ], actual_response)
        
        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges
        validate = TestConsumer()

        validations = all([
            validate.host_validate(collections.get('hostname')), 
            validate.edges_validate(edges.get('asset_hostname')),
        ])
        assert validations is True
    
    @patch('car_framework.car_service.CarService.graph_search')
    @patch('car_framework.car_service.CarService.graph_attribute_search')
    @patch('connector.server_access.AssetServer.get_db_instances')
    @patch('connector.server_access.AssetServer.get_db_instances')
    @patch('connector.server_access.AssetServer.event_logs')
    def test_create_database_update(self, mock_cloudtrail_events, mock_db_data, search_data, attribute_search, db_graph_data):
        """Unit test case for create RDS database"""
        mock_cloudtrail_events.return_value = JsonResponse(200, 'db_cloutrail_events.json').json()
        for item in mock_cloudtrail_events.return_value:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        mock_db_data.return_value = JsonResponse(200, 'db_list_log.json').json()
        search_data.return_value = JsonResponse(200, 'db_search.json').json()
        db_graph_data.return_value = JsonResponse(200, 'db_car_search.json').json()
        attribute_search.return_value = [{'external_id': ['AWS-TEST:db-GQNFWUQIV7BLAFOMGEDTPTN67M'], 'source':['AWS-TEST']}]
        context_patch()
        
        collection_create, collection_modify = context().data_collector.create_database(incremental=True)
        assert collection_create is not None
        assert collection_modify is not None

        context().inc_importer.handle_data([
            'asset_database',
            'asset',
            'hostname',
            'asset_hostname',
            'asset_geolocation',
            'geolocation',
            'application',
            'asset_application',
        ], collection_modify)

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

    @patch('connector.server_access.AssetServer.security_alerts_update')
    def test_create_vulnerability_update(self, mock_alerts_response):
        """Unit test for create vulnerability update"""
        mock_alerts_response.return_value = JsonResponse(200, 'alerts_log.json').json()['Findings']
        
        context_patch()

        actual_response = context().data_collector.create_vulnerability(incremental=True)
        
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

    @patch('connector.server_access.AssetServer.get_instances')
    @patch('connector.server_access.AssetServer.container_ec2_instance')
    @patch('car_framework.car_service.CarService.graph_attribute_search', return_value=Mock())
    @patch('connector.server_access.AssetServer.list_running_containers')
    @patch('connector.server_access.AssetServer.event_logs', return_value=Mock())
    def test_container_update_delete(self, mock_event_details, mock_container_list, mock_graph_search,
                                     mock_container_instances, mock_get_instances):
        """Unit test cases for container incremental"""
        context_patch()
        stop_task = JsonResponse(200, 'stop_task.json').json()
        delete_container_log = JsonResponse(200, 'deregister_instances.json').json()
        delete_cluster = JsonResponse(200, 'delete_cluster.json').json()
        run_task = JsonResponse(200, 'run_task.json').json()
        register_instances = JsonResponse(200, 'register_instances.json').json()
        container_task_cluster = JsonResponse(200, 'container_task_cluster_id.json').json()
        running_containers = JsonResponse(200, 'describe_tasks.json').json()
        container_instances = JsonResponse(200, 'describe_container_instances.json').json()
        get_instances = JsonResponse(200, 'get_instance.json').json()
        for item in stop_task:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in delete_container_log:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in delete_cluster:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in run_task:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in register_instances:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        mock_event_details.side_effect = [stop_task, delete_container_log, delete_cluster, run_task, register_instances]
        mock_container_list.return_value = running_containers
        mock_graph_search.return_value = container_task_cluster
        mock_container_instances.return_value = container_instances
        mock_get_instances.return_value = get_instances
        
        response = context().data_collector.create_container(incremental=True)
        if response:
            context().inc_importer.handle_data([
                'container',
                'asset_container',
            ], response)

        collections = context().inc_importer.data_handler.collections
        edges = context().inc_importer.data_handler.edges

        container = TestConsumer()
        validations = all([
            container.container_validate(collections.get('container')), 
            container.edges_validate(edges.get('asset_container'))
        ])

        assert validations is True
        assert response is not None
        assert len(collections.get('container')) is 6
        assert len(edges.get('asset_container')) is 12

    @patch('connector.data_collector.DataCollector.ec2_instances')
    @patch('car_framework.car_service.CarService.graph_search')
    @patch('connector.server_access.AssetServer.get_instances')
    def test_update_network_interface(self, mock_instance_details, mock_graph_details, mock_ec2_instance):
        """Unit test cases for network interface incremental"""
        context_patch()
        instances = JsonResponse(200, 'get_instance.json').json()
        mock_graph_details.return_value = JsonResponse(200, 'graph_search_log.json').json()
        mock_instance_details.return_value = instances
        mock_ec2_instance.return_value = {'test-instance-i1a'}

        actual_response = context().data_collector.update_network_data()
        assert actual_response is not None
        for item in actual_response:
            assert isinstance(item['Placement']['AvailabilityZone'], str)
            assert 'networkData', 'NetworkInterfaces' in item

    @patch('car_framework.car_service.CarService.graph_search')
    @patch('car_framework.car_service.CarService.graph_attribute_search')
    @patch('connector.server_access.AssetServer.list_applications_env')
    @patch('connector.server_access.AssetServer.event_logs')
    def test_app_swap_host(self, mock_event_logs, mock_app_details, mock_attr_details, mock_graph_details):
        """Unit test cases for application host incremental update"""
        context_patch()
        swap_env_log = JsonResponse(200, 'swap_env_log.json').json()
        for item in swap_env_log:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        mock_event_logs.return_value = swap_env_log
        mock_app_details.return_value = JsonResponse(200, 'environment_log.json').json()
        mock_attr_details.return_value = [{'external_id': 'AWS-TEST:test-external-123', 'source': 'AWS-TEST'}]
        mock_graph_details.return_value['result'] = {"name": "app-name"}
        mock_graph_details.return_value['related'] = []

        actual_response = context().data_collector.application_swap_host()
        assert actual_response is not None
        for item in actual_response:
            assert isinstance(item['ResourceId'], str)
            assert 'networkData' in item

    @patch('connector.data_collector.DataCollector.interface_create_id')
    @patch('botocore.client.BaseClient._make_api_call')
    @patch('connector.server_access.AssetServer.event_logs', return_value=Mock())
    def test_update_ipv4_ipv6(self, mock_event_logs, mock_network_interfaces, mock_interface):
        """Unit test cases for ip incremental update"""
        context_patch()
        private_ip_logs = JsonResponse(200, 'assign_private_log.json').json()
        ipv6_update = JsonResponse(200, 'assign_private_ipv6_log.json').json()
        ipv6_delete = JsonResponse(200, 'unassign_private_ipv6_log.json').json()
        for item in private_ip_logs:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in ipv6_update:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        for item in ipv6_delete:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])

        mock_event_logs.side_effect = [private_ip_logs, ipv6_update, ipv6_delete]
        mock_network_interfaces.return_value = JsonResponse(200, 'ntwrk_interface_log.json').json()
        mock_interface.return_value = {'vpc-10db926a'}

        context().data_collector.update_private_ipv4()

    @patch('car_framework.car_service.CarService.graph_search')
    @patch('connector.server_access.AssetServer.get_db_instances')
    def test_database_update(self, mock_db_data, db_graph_data):
        """Unit test cases for RDS database incremental"""
        context_patch()
        mock_db_data.return_value = JsonResponse(200, 'db_search.json').json()
        db_graph_data.return_value = JsonResponse(200, 'db_car_search.json').json()
        modify_db = ['db-SW7U4PNNHP5K4FSQ7SVHYOJH6E', 'db-GQNFWUQIV7BLAFOMGEDTPTN67M']
        response = context().data_collector.database_update(modify_db, list())
        for item in response:
            assert isinstance(item['DBInstanceIdentifier'], str)
            assert 'DBInstanceArn', 'DbiResourceId' in item
            assert isinstance(item['AvailabilityZone'], str)
        assert response is not None
