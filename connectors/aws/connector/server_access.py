import json
from datetime import datetime, timedelta
import boto3

from car_framework.context import context
from car_framework.util import DatasourceFailure
from car_framework.server_access import BaseAssetServer

# This is to disable context().fooMember error in IDE
# pylint: disable=no-member

class AssetServer(BaseAssetServer):
    """Client object for Boto3"""
    def __init__(self):
        self.region_name = context().args.CONNECTION_REGION
        self.aws_access_key_id = context().args.CONFIGURATION_AUTH_AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = context().args.CONFIGURATION_AUTH_AWS_SECRET_ACCESS_KEY

    def test_connection(self):
        try:
            self.get_instances()
            code = 0
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    def getClient(self, service_name):
        return boto3.client(service_name, aws_access_key_id=self.aws_access_key_id,
                                   aws_secret_access_key=self.aws_secret_access_key,
                                   region_name=self.region_name)

    def getResource(self, service_name):
        return boto3.resource(service_name, aws_access_key_id=self.aws_access_key_id,
                                   aws_secret_access_key=self.aws_secret_access_key,
                                   region_name=self.region_name)
        
    def get_instances(self, instance_ids=None):
        """
        :return: describe instances from ec2
        """
        try:
            ec2_list = list()
            client = self.getClient('ec2')
            paginator = client.get_paginator('describe_instances')
            if instance_ids is not None:
                response_data = paginator.paginate(InstanceIds=instance_ids)
            else:
                response_data = paginator.paginate()
            if response_data:
                for page in response_data:
                    ec2_list.extend(page['Reservations'])
            return ec2_list
        except Exception as ex:
            context().logger.error("Error when getting AWS resource get_instances")
            raise DatasourceFailure(ex)

    def security_alerts(self, ec2_id):
        """Security alerts from security hub"""
        try:
            data_list = list()
            ec2 = self.getClient('securityhub')
            paginator = ec2.get_paginator('get_findings')
            response_iterator = paginator.paginate(Filters={
                'ResourceId': [
                    {
                        'Value': str(ec2_id),
                        'Comparison': 'EQUALS'
                    }]})
            for page in response_iterator:
                data_list.extend(page['Findings'])
            return data_list
        except Exception as ex:
            context().logger.error("Error when getting AWS resource security_alerts")
            raise DatasourceFailure(ex)

    def event_logs(self, attribute_value, attribute_type):
        """Event logs from Cloud trail"""

        try:
            filter_value = [{
                'AttributeKey': attribute_type,
                'AttributeValue': attribute_value}, ]
            logs_collection = []
            logs = self.getClient('cloudtrail')
            paginator = logs.get_paginator('lookup_events')
            response_data = paginator.paginate(LookupAttributes=filter_value,
                                               StartTime=self.epoch_to_datetime_conv(context().last_model_state_id),
                                               EndTime=self.epoch_to_datetime_conv(context().new_model_state_id))
            for page in response_data:
                logs_collection.extend(page['Events'])
            return logs_collection
        except Exception as ex:
            context().logger.error("Error when getting AWS resource event_logs")
            raise DatasourceFailure(ex)

    def security_alerts_update(self, status, value):
        """security alerts for incremental update"""

        try:
            ec2 = self.getClient('securityhub')
            paginator = ec2.get_paginator('get_findings')
            current_date = self.datetime_format_to_ISO_8601(self.epoch_to_datetime_conv(context().new_model_state_id))
            last_current_date = self.datetime_format_to_ISO_8601(self.epoch_to_datetime_conv(context().last_model_state_id))

            if status == 'create':
                create_list = list()
                response_iterator_create = paginator.paginate(
                    Filters={
                        'ResourceType': [{'Value': str(value), 'Comparison': 'EQUALS'}],
                        'CreatedAt': [{
                            'Start': last_current_date,
                            'End': current_date
                        }]
                    })
                for page in response_iterator_create:
                    create_list.extend(page['Findings'])
                return create_list

            elif status == 'update':
                update_list = list()
                start_date = self.datetime_format_to_ISO_8601(self.epoch_to_datetime_conv(context().new_model_state_id) - timedelta(days=365))
                response_iterator = paginator.paginate(
                    Filters={
                        'ResourceType': [{'Value': str(value), 'Comparison': 'EQUALS'}],
                        'UpdatedAt': [{
                            'Start': last_current_date,
                            'End': current_date
                        }],
                        'CreatedAt': [{
                            'Start': start_date,
                            'End': last_current_date
                        }]
                    })
                for page in response_iterator:
                    update_list.extend(page['Findings'])
                return update_list

            elif status == 'delete':
                start_date = self.datetime_format_to_ISO_8601(self.epoch_to_datetime_conv(context().new_model_state_id) - timedelta(days=365))
                end_date = self.datetime_format_to_ISO_8601(self.epoch_to_datetime_conv(context().new_model_state_id) - timedelta(days=80))
                delete_list = list()
                response_iterator_delete = paginator.paginate(
                    Filters={
                        'ResourceType': [{'Value': str(value), 'Comparison': 'EQUALS'}], 
                        'UpdatedAt': [{
                            'Start': start_date,
                            'End': end_date
                        }]
                    })
                for page in response_iterator_delete:
                    delete_list.extend(page['Findings'])
                return delete_list
        except Exception as ex:
            context().logger.error("Error when getting AWS resource security_alerts_update")
            raise DatasourceFailure(ex)

    def list_applications(self, app_name=None):
        """List application"""

        try:
            client = self.getClient('elasticbeanstalk')
            if app_name:
                app_response = client.describe_applications(ApplicationNames=app_name)
                return app_response['Applications']

            elif not app_name:
                app_response = client.describe_applications()
                return app_response['Applications']
        except Exception as ex:
            context().logger.error("Error when getting AWS resource list_applications")
            raise DatasourceFailure(ex)

    def list_applications_env(self, app_name=None, env_name=None, env_id=None):
        """List application environment"""
        try:
            client = self.getClient('elasticbeanstalk')
            if env_name:
                app_response = client.describe_environments(ApplicationName=app_name, EnvironmentNames=[env_name])
                return app_response
            elif env_id:
                env_response = client.describe_environments(EnvironmentIds=env_id)
                return env_response
            else:
                env_list = list()
                paginator = client.get_paginator('describe_environments')
                response_data = paginator.paginate(ApplicationName=app_name)
                for page in response_data:
                    env_list.extend(page['Environments'])
                return env_list
        except Exception as ex:
            context().logger.error("Error when getting AWS resource list_applications_env")
            raise DatasourceFailure(ex)

    def get_db_instances(self, resource_ids=None, instance_identifier=None):
        """list the RDS database instances"""
        try:
            db_list = list()
            rds_client = self.getClient('rds')
            paginator = rds_client.get_paginator('describe_db_instances')

            if resource_ids:
                response_data = paginator.paginate(Filters=[{'Name': 'dbi-resource-id', 'Values': resource_ids}])
            elif instance_identifier:
                response_data = paginator.paginate(DBInstanceIdentifier=instance_identifier)
            else:
                response_data = paginator.paginate()
            for page in response_data:
                db_list.extend(page['DBInstances'])
            return db_list
        except Exception as ex:
            context().logger.error("Error when getting AWS resource get_db_instances")
            raise DatasourceFailure(ex)

    def get_image_name(self, image_id):
        """get the name details of image id"""
        try:
            client = self.getResource('ec2')
            response = client.Image(image_id)
            return response.name
        except Exception as ex:
            context().logger.debug("Failed to get image id %s", ex)
            return image_id

    def get_network_interface(self, interface_id):
        """Get Network Interface Details using interface id"""
        try:
            client = self.getClient('ec2')
            response = client.describe_network_interfaces(NetworkInterfaceIds=interface_id)
            return response
        except Exception as ex:
            context().logger.debug("Failed to get interface id %s", ex)
            return None

    def list_running_containers(self, cluster_arn=None, task_arn=None):
        """list containers"""
        try:
            client = self.getClient('ecs')
            app_response = None
            list_cluster = list()
            paginator = client.get_paginator('list_clusters')
            response = paginator.paginate()
            for page in response:
                list_cluster.extend(page['clusterArns'])
            task_list = []
            app_response = []
            for cluster in list_cluster:
                paginator = client.get_paginator('list_tasks')
                response = paginator.paginate(cluster=cluster)
                for page in response:
                    task_list.extend(page['taskArns'])
                for i in range(0, len(task_list), 100):
                    task_data = client.describe_tasks(cluster=cluster, tasks=task_list[i:i+100])
                    app_response.extend(task_data['tasks'])
            return app_response

        except Exception as ex:
            context().logger.error("Error when getting AWS resource list_running_containers")
            raise DatasourceFailure(ex)

    # def list_running_containers2(self, cluster_arn=None, task_arn=None):
    #     """list containers"""

    #     try:
    #         client = self.getClient('ecs')
    #         app_response = client.describe_tasks(cluster=cluster_arn, tasks=[task_arn])
    #         return app_response

    #     except Exception as ex:
    #         context().logger.error("Error when getting AWS resource list_running_containers")
    #         raise DatasourceFailure(ex)

    def container_ec2_instance(self, cluster_arn=None, container_instance_arn=None):
        """Security alerts from security hub"""
        try:
            client = self.getClient('ecs')
            app_response = client.describe_container_instances(cluster=cluster_arn,
                                                               containerInstances=[container_instance_arn])
            return app_response
        except Exception as ex:
            context().logger.error("Error when getting AWS resource container_ec2_instance")
            raise DatasourceFailure(ex)

    def get_incremental_time(self):
        """store the incremental time for next run"""
        try:
            client = self.getClient('cloudtrail')
            response = client.lookup_events(MaxResults=1)
            for values in response['Events']:
                values['CloudTrailEvent'] = json.loads(values['CloudTrailEvent'])
                time = values['CloudTrailEvent']['eventTime']
                last_run = self.converted_time(time) + timedelta(seconds=1)
                last_runtime = self.convert_to_tz(str(last_run))
                return last_runtime

        except Exception as ex:
            context().logger.error("Error when getting AWS resource get_incremental_time")
            raise DatasourceFailure(ex)


    @staticmethod
    def converted_time(time_string):
        """convert string to datetime object"""
        time = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
        return time

    @staticmethod
    def convert_to_tz(time_string):
        """convert time to tz format"""
        time = datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S')
        tz_time = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        return tz_time

    @staticmethod
    def timestamp_to_epoch_conv(time_string):
        time_pattern = "%Y-%m-%dT%H:%M:%S"
        epoch = datetime(1970, 1, 1)
        converted_time = int(((datetime.strptime(str(time_string)[:19], time_pattern) - epoch).total_seconds()) * 1000)
        return converted_time

    @staticmethod
    def epoch_to_datetime_conv(epoch_time):
        epoch_time = float(epoch_time) / 1000.0
        datetime_time = datetime.fromtimestamp(epoch_time)
        return datetime_time

    @staticmethod
    def datetime_format_to_ISO_8601(dt):
        time_pattern = "%Y-%m-%dT%H:%M:%S"
        return dt.strftime(time_pattern)