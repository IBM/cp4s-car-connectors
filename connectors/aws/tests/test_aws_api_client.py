"""Unit Test Case for AWS Api Client"""

import os
import unittest
import json
from unittest.mock import patch

from tests.common_validate import context, context_patch, JsonResponse, MockJsonResponse, JsonTextResponse

TEST_DIR = os.path.dirname(os.path.realpath(__file__))

@patch('botocore.client.BaseClient._make_api_call')
class TestAwsApiClient(unittest.TestCase):
    """Unit test cases for Api Client"""
    
    def test_get_instances(self, mock_client_details):
        """unit test for get ec2 instances"""
        context_patch()
        instance_list, response_list, flag = list(), list(), False
        instance_details = JsonResponse(200, 'Instance_details.json').json()
        create_events = JsonResponse(200, 'cloudtrail_run_instance_events.json').json()
        mock_client_details.side_effect = [instance_details, create_events, instance_details, create_events]
        actual_response, actual_create_events = context().asset_server.get_instances(None)
        instance_response, instance_create_events = context().asset_server.get_instances('instance-123')

        assert all([e['EventName'] == 'RunInstances' for e in actual_create_events])
        assert all([e['EventName'] == 'RunInstances' for e in instance_create_events])

        for item in actual_response:
            if 'Instances' in item:
                flag = True
            response_list.append(flag)
        for item in instance_response:
            if 'Instances' in item:
                flag = True
            instance_list.append(flag)
        assert all(instance_list), all(response_list) is True
        assert instance_response, actual_response is not None

    def test_get_instances_exception(self, mock_log_details):
        """Unit test for get ec2 instance details exception"""
        context_patch()
        mock_log_details.side_effect = Exception('An error occurred (InvalidClientTokenId) when calling the '
                                                 'Describeinstances operation: The security token included in the '
                                                 'request is invalid.')
        with self.assertRaises(Exception) as error:
            context().asset_server.get_instances()
        the_exception = error.exception
        assert the_exception.args[0] is mock_log_details.side_effect

    def test_security_alerts(self, mock_client_details):
        """unit test for security alerts."""
        context_patch()
        alerts_list, flag = list(), True
        mock_client_details.return_value = JsonResponse(200, 'alerts_log.json').json()
        actual_response = context().asset_server.security_alerts('alerts-ec2')
        for item in actual_response:
            if 'Findings' in item:
                flag = True
            alerts_list.append(flag)
        assert all(alerts_list) is True
        assert actual_response is not None

    def test_event_logs(self, mock_client_details):
        """Unit test for lookup event logs"""
        context_patch()
        event_list, flag = list(), False
        mock_client_details.return_value = JsonResponse(200, 'events_log.json').json()
        actual_response = context().asset_server.event_logs('EventName', 'test_data')
        for item in actual_response:
            if 'CloudTrailEvent' in item:
                flag = True
            event_list.append(flag)
        assert all(event_list) is True
        assert actual_response is not None

    def test_event_logs_exception(self, mock_log_details):
        """Unit test for get lookup events exception"""
        context_patch()
        mock_log_details.side_effect = Exception('Could not connect to the endpoint URL.')
        with self.assertRaises(Exception) as error:
            context().asset_server.event_logs('StartInstance', 'EventName')
        the_exception = error.exception
        assert the_exception.args[0] is mock_log_details.side_effect
        

    def test_security_alerts_update(self, mock_client_details):
        """Unit test for security alerts update"""
        context_patch()
        create_list, update_list, delete_list, flag = list(), list(), list(), False
        mock_client_details.return_value = JsonResponse(200, 'alerts_log.json').json()
        alerts_create_response = context().asset_server.security_alerts_update('create', 'RDS')
        alerts_update_response = context().asset_server.security_alerts_update('update', 'RDS')
        alerts_delete_response = context().asset_server.security_alerts_update('delete', 'RDS')
        for item in alerts_create_response:
            if 'Resources' in item:
                flag = True
            create_list.append(flag)
        for item in alerts_update_response:
            if 'Resources' in item:
                flag = True
            update_list.append(flag)
        for item in alerts_delete_response:
            if 'Resources' in item:
                flag = True
            delete_list.append(flag)
        assert all(create_list), all(update_list) is True
        assert all(delete_list) is True
        assert alerts_create_response, alerts_update_response is not None
        assert alerts_delete_response is not None

    def test_security_alerts_exception(self, mock_log_details):
        """Unit test for get security alerts exception"""
        context_patch()
        mock_log_details.side_effect = Exception('Could not connect to the endpoint URL.')
        with self.assertRaises(Exception) as error:
            context().asset_server.security_alerts_update('create', 'AWSEc2Instance')
        the_exception = error.exception
        with self.assertRaises(Exception) as error:
            context().asset_server.security_alerts("")
        sr_exception = error.exception
        assert the_exception.args[0] is mock_log_details.side_effect
        assert sr_exception.args[0] is mock_log_details.side_effect

    def test_db_instances(self, mock_client_details):
        """Unit test for list RDS database"""
        context_patch()
        database_log = JsonResponse(200, 'database_log.json').json()
        create_events = JsonResponse(200, 'cloudtrail_create_db_instance_events.json').json()
        mock_client_details.side_effect = [database_log, create_events, database_log, create_events, database_log, create_events]

        actual_response, actual_create_events = context().asset_server.get_db_instances(['db-GQNFWUQIV7BL'])
        actual_response1, actual_create_events1 = context().asset_server.get_db_instances(instance_identifier=['test-db'])
        actual_response2, actual_create_events2 = context().asset_server.get_db_instances()

        assert all([e['EventName'] == 'CreateDBInstance' for e in actual_create_events])
        assert all([e['EventName'] == 'CreateDBInstance' for e in actual_create_events1])
        assert all([e['EventName'] == 'CreateDBInstance' for e in actual_create_events2])

        assert actual_response[0]['DBInstanceIdentifier'] is not None
        assert actual_response and actual_response1 and actual_response2 is not None

    def test_get_db_exception(self, mock_log_details):
        """Unit test for get RDS database exception"""
        context_patch()
        mock_log_details.side_effect = Exception('An error occurred (SignatureDoesNotMatch) when calling the '
                                                 'DescribeDBInstances operation: The request signature we calculated '
                                                 'does not match the signature you provided. Check your AWS Secret '
                                                 'Access Key and signing method. Consult the service documentation '
                                                 'for details.')
        with self.assertRaises(Exception) as error:
            context().asset_server.get_db_instances(['db-GQNFWUQIV7BL'])
        the_exception = error.exception
        assert the_exception.args[0] is mock_log_details.side_effect

    def test_list_applications(self, mock_client_details):
        """Unit test for list applications"""
        context_patch()
        app_valid_list, flag = list(), False
        application_log = JsonResponse(200, 'application_log.json').json()
        create_events = JsonResponse(200, 'cloudtrail_create_application_events.json').json()
        mock_client_details.side_effect = [application_log, create_events, application_log, create_events]

        actual_response, actual_create_events = context().asset_server.list_applications('testapp')
        actual_response_app, actual_create_events_app = context().asset_server.list_applications()

        assert all([e['EventName'] == 'CreateApplication' for e in actual_create_events])
        assert all([e['EventName'] == 'CreateApplication' for e in actual_create_events_app])

        for item in actual_response:
            if 'ApplicationName' in item and 'ApplicationArn' in item:
                flag = True
            app_valid_list.append(flag)
        for item in actual_response_app:
            if 'ApplicationName' in item and 'ApplicationArn' in item:
                flag = True
            app_valid_list.append(flag)
        assert all(app_valid_list) is True
        assert actual_response is not None

    def test_list_applications_exception(self, mock_log_details):
        """Unit test for get application details exception"""
        context_patch()
        mock_log_details.side_effect = Exception('An error occurred (SignatureDoesNotMatch) when calling the '
                                                 'DescribeApplications operation: The request signature we calculated '
                                                 'does not match the signature you provided. Check your AWS Secret '
                                                 'Access Key and signing method. Consult the service documentation '
                                                 'for details.')
        with self.assertRaises(Exception) as error:
            context().asset_server.list_applications()
        the_exception = error.exception
        assert the_exception.args[0] is mock_log_details.side_effect

    def test_list_applications_env(self, mock_client_details):
        """Unit test for list applications env"""
        context_patch()
        env_list, flag = list(), False
        mock_client_details.return_value = JsonResponse(200, 'environment_log.json').json()
        actual_response = context().asset_server.list_applications_env('pythonsample', 'test_env')
        app_response = context().asset_server.list_applications_env('pythonsample')
        env_response = context().asset_server.list_applications_env(env_id='e-id123')
        for item in actual_response['Environments']:
            if item["CNAME"] and isinstance(item["CNAME"], str):
                flag = True
            env_list.append(flag)
        for item in app_response:
            if item["CNAME"] and isinstance(item["CNAME"], str):
                flag = True
            env_list.append(flag)
        for item in env_response['Environments']:
            if item["CNAME"] and isinstance(item["CNAME"], str):
                flag = True
            env_list.append(flag)
        assert all(env_list) is True
        assert actual_response, app_response is not None

    def test_list_applications_env_exception(self, mock_log_details):
        """Unit test for get application environment details exception"""
        context_patch()
        mock_log_details.side_effect = Exception('An error occurred (SignatureDoesNotMatch) when calling the '
                                                 'DescribeEnvironments operation: The request signature we calculated '
                                                 'does not match the signature you provided. Check your AWS Secret '
                                                 'Access Key and signing method. Consult the service documentation '
                                                 'for details.')
        with self.assertRaises(Exception) as error:
            context().asset_server.list_applications_env()
        the_exception = error.exception
        assert the_exception.args[0] is mock_log_details.side_effect


    def test_get_network_interface(self, mock_client_details):
        """Unit test for network interface"""
        context_patch()
        network_list, flag = list(), False
        mock_client_details.return_value = JsonResponse(200, 'ntwrk_interface_log.json').json()
        actual_response = context().asset_server.get_network_interface('interface-123')
        for item in actual_response['NetworkInterfaces']:
            if 'Ipv6Addresses' in item:
                flag = True
            else: 
                flag = False
            network_list.append(flag)
        assert all(network_list) is True
        assert actual_response is not None

    def test_list_running_containers(self, mock_client_details):
        """Unit test for list running containers"""
        context_patch()
        list_clusters = JsonResponse(200, 'list_clusters.json').json()
        list_tasks = JsonResponse(200, 'list_tasks.json').json()
        describe_tasks = JsonResponse(200, 'describe_tasks.json').json()
        create_events = JsonResponse(200, 'cloudtrail_create_cluster_events.json').json()
        mock_client_details.side_effect = [list_clusters, list_tasks, describe_tasks, create_events]

        actual_response, actual_create_events = context().asset_server.list_running_containers('cluster-arn', 'task-arn')

        assert all([e['EventName'] == 'CreateCluster' for e in actual_create_events])

        for item in actual_response:
            assert isinstance(item['availabilityZone'], str)
            assert 'containers' in item
        assert actual_response is not None


    def test_container_ec2_instance(self, mock_client_details):
        """Unit test for container ec2 instances"""
        context_patch()
        describe_container_instances = JsonResponse(200, 'describe_container_instances.json').json()
        mock_client_details.return_value = describe_container_instances
        actual_response = context().asset_server.container_ec2_instance('cluster-arn', 'cluster_instance_arn')
        for item in actual_response['containerInstances']:
            assert isinstance(item['containerInstanceArn'], str)
        assert 'containerInstances' in actual_response
        assert actual_response is not None

    def test_image_name(self, mock_client_details):
        """Unit test for image name"""
        context_patch()
        mock_client_details.return_value = 'Test-id'
        actual_response = context().asset_server.get_image_name('Test-id')
        assert isinstance(actual_response, str)
        assert actual_response is not None

    def test_get_incremental_time(self, mock_cloudtrail_events):
        """Unit test for get incremental time"""
        context_patch()
        mock_cloudtrail_events.return_value = JsonResponse(200, 'cloud_trail_event.json').json()
        for item in mock_cloudtrail_events.return_value['Events']:
            item['CloudTrailEvent'] = json.dumps(item['CloudTrailEvent'])
        actual_response = context().asset_server.get_incremental_time()
        assert actual_response is not None

    def test_get_time_exception(self, mock_cloudtrail_events):
        """Unit test for get last run time exception"""
        context_patch()
        mock_cloudtrail_events.side_effect = Exception('An error occurred (SignatureDoesNotMatch) when calling the '
                                                       'LookupEvents operation: The request signature we calculated '
                                                       'does not match the signature you provided. Check your AWS '
                                                       'Secret Access Key and signing method. Consult the service '
                                                       'documentation for details.')
        with self.assertRaises(Exception) as error:
            context().asset_server.get_incremental_time()
        the_exception = error.exception
        assert the_exception.args[0] is mock_cloudtrail_events.side_effect
