import json
from car_framework.context import context

# This is to disable context().fooMember error in IDE
# pylint: disable=no-member
def deep_get(_dict, keys, default=None):
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict

class DataCollector(object):
    _collected_data = {}
    ec2_create = list()
    ec2_instances, delete_attachment_id, interface_create_id = set(), set(), set()
    
    # to-be-updated entries
    vertices_update, edges_update = list(), list()
    # to-be-deleted entries
    asset_delete, ip_delete, dns_delete, vuln_delete = list(), list(), list( ),list()
    database_delete, app_delete, container_delete = list(), list(), list()

    def _get_collected_data(self, data):
        if not self._collected_data.get(data):
            if data == 'vm':
                self._collected_data[data] = context().asset_server.get_instances()
            elif data == 'db':
                self._collected_data[data] = context().asset_server.get_db_instances()
            elif data == 'app':
                self._collected_data[data] = context().asset_server.list_applications()
            elif data == 'container':
                self._collected_data[data] = context().asset_server.list_running_containers()
        
        return self._collected_data[data]

    def create_asset(self, incremental=True):
        """Creating EC2 asset and network interface"""
        context().logger.info('Collecting assets')
        data = None
        asset_list = []
        # incremental import case
        if incremental:
            asset_create = self.asset_create_delete()
            self.incremental_create_tags()

            if asset_create:
                data = context().asset_server.get_instances(asset_create)
        else:
            data = self._get_collected_data('vm')

        if data:
            for instances in data:
                for instance in instances['Instances']:
                    if deep_get(instance, ['State', 'Name']) != 'terminated':
                        resource_id = 'arn:aws:ec2:' + instance['Placement']['AvailabilityZone'][:-1] + ':' + \
                                    context().args.accountId + ':instance/' + instance['InstanceId']
                        instance['ResourceId'] = resource_id
                        image_name = context().asset_server.get_image_name(instance['ImageId'])
                        instance['ImageName'] = str(image_name)
                        if 'NetworkInterfaces' in instance:
                            processed_data = self.network_interface_process(instance)
                            if processed_data and deep_get(instance, ['Tags']):
                                for values in instance['Tags']:
                                    if values['Key'] == 'elasticbeanstalk:environment-id':
                                        processed_data['EnvironmentId'] = values['Value']
                                        env_data = context().asset_server.list_applications_env(
                                            env_id=[processed_data['EnvironmentId']])
                                        for env in env_data['Environments']:
                                            app_arn_data = context().asset_server.list_applications([env['ApplicationName']])
                                            if deep_get(env, ['CNAME']):
                                                temp = dict()
                                                temp['env_host'] = env['CNAME']
                                                processed_data['networkData'].append(temp)
                                            for app in app_arn_data:
                                                processed_data['ApplicationArn'] = app['ApplicationArn']
                            asset_list.append(processed_data)
        return asset_list


    # database node creation utility
    def create_database(self, incremental=True):
        """Database creation"""
        context().logger.info('Collecting databases')
        data_create = None
        data_modify = None
        if incremental:
            response_data = self.database_update_delete()
            data_create = deep_get(response_data, ['create'])
            data_modify = deep_get(response_data, ['modify'])
        else:
            data_create = self._get_collected_data('db')

        return data_create, data_modify

    def create_application(self, incremental=True):
        """Beanstalk application creation"""
        context().logger.info('Collecting applications')
        data = None
        hosts_modify = []
        app_list = []
        if incremental:
            create_app_name = []
            self.application_update(create_app_name)  # create/delete app
            hosts_modify = self.application_swap_host()  # update hostname
            if create_app_name:
                data = context().asset_server.list_applications(create_app_name)
        else:
            data = self._get_collected_data('app')

        if data:
            for app in data:
                app_list.append(app)

        return app_list, hosts_modify


    def create_container(self, incremental=True):
        context().logger.info('Collecting containers')
        data = None
        container_list = []
        if incremental:
            container_list = self.container_update_delete()
        else:
            data = self._get_collected_data('container')
            if data:
                for task in data:
                    if task['lastStatus'] == 'RUNNING' and task['launchType'] == 'EC2':
                        processed_data = self.process_task_container(task)
                        container_list.append(processed_data)

        return container_list

    # vulnerability node creation utility
    def create_vulnerability(self, incremental=True):
        """Vulnerability report for EC2"""
        context().logger.info('Collecting vulnerabilities')
        vuln_list = []
        if incremental:  # incremental import case
            vuln_list = context().asset_server.security_alerts_update('create', 'AwsEc2Instance')
            data_security_update = context().asset_server.security_alerts_update('update', 'AwsEc2Instance')
            data_security_delete = context().asset_server.security_alerts_update('delete', 'AwsEc2Instance')
            for value in data_security_update:
                temp = dict()
                temp['from'] = context().args.source + ':' + value['Resources'][0]['Id']
                temp['to'] = context().args.source + ':' + value['Id']
                temp['edge_type'] = 'asset_vulnerability'
                temp['last_modified'] = context().asset_server.timestamp_to_epoch_conv(value['UpdatedAt'])
                self.edges_update.append(temp)
            for delete_ids in data_security_delete:
                self.vuln_delete.append(delete_ids['Id'])
        else:  # initial import case
            data = self._get_collected_data('vm')
            for instances in data:
                for instance in instances['Instances']:
                    resource_id = 'arn:aws:ec2:' + instance['Placement']['AvailabilityZone'][:-1] + ':' + \
                                context().args.accountId + ':instance/' + instance['InstanceId']
                    data = context().asset_server.security_alerts(resource_id)
                    vuln_list.extend(data)
                    
        return vuln_list

    # FROM INCREMENTAL
    def create_network(self):
        """EC2 network interface updates"""
        context().logger.info('Collecting network data')
        # incremental New Interface Create/Delete import case
        self.network_interface_delete()
        interface_list = self.secondary_network_interface_create()
        self.get_attachment_data()

        # incremental New Ip Create/Delete import case
        private_ipv4_host_update = self.update_public_ip()

        return interface_list, private_ipv4_host_update

    """EC2 Incremental logic"""
    def asset_create_delete(self):
        """asset create and delete"""
        # asset delete
        delete_asset_logs = context().asset_server.event_logs('TerminateInstances', 'EventName')
        for vm_log in delete_asset_logs:
            vm_log['CloudTrailEvent'] = json.loads(vm_log['CloudTrailEvent'])
            for resource_id in vm_log['Resources']:
                if resource_id['ResourceType'] == 'AWS::EC2::Instance' and deep_get(vm_log,
                                                                                    ['CloudTrailEvent',
                                                                                    'errorCode']) is None:
                    resource_id = 'arn:aws:ec2:' + deep_get(vm_log, ['CloudTrailEvent', 'awsRegion']) + ':' + \
                                context().args.accountId + ':instance/' + resource_id['ResourceName']
                    self.asset_delete.append(resource_id)

        # asset create
        create_asset_logs = context().asset_server.event_logs('RunInstances', 'EventName')
        for vm_log in create_asset_logs:
            vm_log['CloudTrailEvent'] = json.loads(vm_log['CloudTrailEvent'])
            for resource_id in vm_log['Resources']:
                if resource_id['ResourceType'] == 'AWS::EC2::Instance' and deep_get(vm_log, ['CloudTrailEvent',
                                                                                            'errorCode']) is None:
                    arn_id = 'arn:aws:ec2:' + deep_get(vm_log, ['CloudTrailEvent', 'awsRegion']) + ':' + \
                            context().args.accountId + ':instance/' + resource_id['ResourceName']
                    if arn_id not in self.asset_delete:
                        self.ec2_create.append(resource_id['ResourceName'])
                    elif arn_id in self.asset_delete:
                        self.asset_delete.remove(arn_id)
        return self.ec2_create


    def update_public_ip(self):
        """Public ip update fetching"""
        # Public Ip Create/Delete
        event_names = ['StopInstances', 'StartInstances', 'RebootInstances']
        public_ip_logs = context().asset_server.event_logs('AWS::EC2::Instance', 'ResourceType')
        for event in public_ip_logs:
            event['CloudTrailEvent'] = json.loads(event['CloudTrailEvent'])
            if event['EventName'] in event_names:
                for resource_id in event['Resources']:
                    if resource_id['ResourceType'] == 'AWS::EC2::Instance' and resource_id['ResourceName'] not in \
                            self.ec2_create:
                        arn_id = 'arn:aws:ec2:' + deep_get(event, ['CloudTrailEvent', 'awsRegion']) + ':' + \
                                context().args.accountId + ':instance/' + resource_id['ResourceName']
                        if arn_id not in self.asset_delete:
                            self.ec2_instances.add(resource_id['ResourceName'])
        self.update_private_ipv4()
        updated_ec2_data = self.update_network_data()
        return updated_ec2_data


    def update_private_ipv4(self):
        """Private ipv4 update fetching"""
        # Private Ipv4 Create/Delete
        event_names = ['AssignPrivateIpAddresses', 'UnassignPrivateIpAddresses']
        interface_collection = set()
        private_ip_logs = context().asset_server.event_logs('AWS::EC2::NetworkInterface', 'ResourceType')
        for ip_log in private_ip_logs:
            ip_log['CloudTrailEvent'] = json.loads(ip_log['CloudTrailEvent'])
            for resource_id in ip_log['Resources']:
                if resource_id['ResourceType'] == 'AWS::EC2::NetworkInterface' and ip_log['EventName'] in event_names and \
                        deep_get(ip_log, ['CloudTrailEvent', 'errorCode']) is None and resource_id['ResourceName'] not \
                        in self.interface_create_id:
                    interface_collection.add(resource_id['ResourceName'])
        self.update_ipv6(interface_collection)


    def update_ipv6(self, interface_collection):
        """Ipv6 update fetching"""
        # Private Ipv6 Create/Delete
        ipv6_update = context().asset_server.event_logs('AssignIpv6Addresses', 'EventName')
        ipv6_delete = context().asset_server.event_logs('UnassignIpv6Addresses', 'EventName')
        ipv6_update.extend(ipv6_delete)
        for item in ipv6_update:
            interface_id = None
            item['CloudTrailEvent'] = json.loads(item['CloudTrailEvent'])
            if deep_get(item, ['CloudTrailEvent', 'responseElements', 'AssignIpv6AddressesResponse',
                            'networkInterfaceId']) and deep_get(item, ['CloudTrailEvent', 'errorCode']) is None:
                interface_id = deep_get(item, ['CloudTrailEvent', 'responseElements', 'AssignIpv6AddressesResponse',
                                            'networkInterfaceId'])
            elif deep_get(item, ['CloudTrailEvent', 'responseElements', 'UnassignIpv6AddressesResponse',
                                'networkInterfaceId']) and deep_get(item, ['CloudTrailEvent', 'errorCode']) is None:
                interface_id = deep_get(item, ['CloudTrailEvent', 'responseElements', 'UnassignIpv6AddressesResponse',
                                            'networkInterfaceId'])
            if interface_id and interface_id not in self.interface_create_id:
                interface_collection.add(interface_id)
        if interface_collection:
            for interface in interface_collection:
                try:
                    network_response = context().asset_server.client.describe_network_interfaces(
                        NetworkInterfaceIds=[interface])
                    for interface_id in network_response['NetworkInterfaces']:
                        if 'Attachment' in interface_id and deep_get(interface_id, ['Attachment', 'InstanceId']) \
                                not in self.ec2_create:
                            self.ec2_instances.add(deep_get(interface_id, ['Attachment', 'InstanceId']))
                except Exception as ex:
                    context().logger.debug("Failed to delete %s", ex)
                    continue


    def update_network_data(self):
        """updating ip and host"""
        # New Network data Create
        update_ip_collection = list()
        if self.ec2_instances:
            ip_logs = context().asset_server.get_instances(instance_ids=list(self.ec2_instances))
            for instances in ip_logs:
                for instance in instances['Instances']:
                    destination_ips, create_ip, create_dns, destination_dns = list(), list(), list(), list()
                    resource_id = 'arn:aws:ec2:' + instance['Placement']['AvailabilityZone'][:-1] + ':' + \
                                context().args.accountId + ':instance/' + instance['InstanceId']
                    if resource_id not in self.asset_delete:
                        instance['ResourceId'] = resource_id
                        processed_data = self.network_interface_process(instance)
                        search_result = context().car_service.graph_search('asset', resource_id, context().args.source)
                        if search_result['result'] and search_result['related']:
                            for car_ip in search_result['related']:
                                if 'ipaddress/' in str(deep_get(car_ip, ["node", "_id"])) and \
                                        deep_get(car_ip, ["node", "_key"]) and context().args.source in \
                                        deep_get(car_ip, ["link", "source"]):
                                    destination_ips.append(deep_get(car_ip, ["node", "_key"]))
                                if 'hostname/' in str(deep_get(car_ip, ["node", "_id"])) and \
                                        deep_get(car_ip, ["node", "_key"]) and context().args.source in \
                                        deep_get(car_ip, ["link", "source"]):
                                    destination_dns.append(deep_get(car_ip, ["node", "_key"]))

                        for values in processed_data['networkData']:
                            create_ip, create_dns = list(), list()
                            for ip_value in values['IpAddress']:
                                if ip_value in destination_ips:
                                    destination_ips.remove(ip_value)
                                elif ip_value not in destination_ips:
                                    create_ip.append(ip_value)
                            values['IpAddress'] = create_ip
                            for dns_value in values['DnsName']:
                                if dns_value in destination_dns:
                                    destination_dns.remove(dns_value)
                                elif dns_value not in destination_dns:
                                    create_dns.append(dns_value)
                            values['DnsName'] = create_dns
                        self.ip_delete.extend(destination_ips)
                        self.dns_delete.extend(destination_dns)
                        update_ip_collection.append(processed_data)
        return update_ip_collection


    def network_interface_process(self, instance):
        """Formatting data source side data's"""
        # formatting Network data source side data
        instance['networkData'] = list()
        for network_data in instance['NetworkInterfaces']:
            if network_data['Attachment']:
                temp = dict()
                count = 0
                for ip_data in network_data['PrivateIpAddresses']:
                    if count == 0:
                        temp['IpAddress'], temp['DnsName'] = list(), list()
                        temp['MacAddress'] = network_data['MacAddress']
                        temp['NetworkInterfaceId'] = network_data['NetworkInterfaceId']
                        temp['AttachmentId'] = deep_get(network_data, ['Attachment', 'AttachmentId'])
                        if deep_get(network_data, ['Association', 'PublicDnsName']) and \
                                deep_get(network_data, ['Association', 'PublicIp']):
                            temp['IpAddress'].append(deep_get(network_data, ['Association', 'PublicIp']))
                            temp['DnsName'].append(deep_get(network_data, ['Association', 'PublicDnsName']))
                        for ipv6 in network_data['Ipv6Addresses']:
                            temp['IpAddress'].append(ipv6['Ipv6Address'])
                    count = count + 1
                    temp['IpAddress'].append(ip_data['PrivateIpAddress'])
                    if 'PrivateDnsName' in ip_data:
                        temp['DnsName'].append(ip_data['PrivateDnsName'])
                instance['networkData'].append(temp)
        return instance


    def secondary_network_interface_create(self):
        """Secondary Network Interface create"""
        # Secondary Network Interface create
        logger = context().logger
        interface_create_data = list()
        flag, interface_id = False, None
        interface_log = context().asset_server.event_logs('AttachNetworkInterface', 'EventName')
        for interface in interface_log:
            interface['CloudTrailEvent'] = json.loads(interface['CloudTrailEvent'])
            for resource_id in interface['Resources']:
                attachment_id = deep_get(interface, ['CloudTrailEvent', 'responseElements', 'attachmentId'])
                if resource_id['ResourceType'] == 'AWS::EC2::NetworkInterface' and attachment_id not in \
                        self.delete_attachment_id and 'errorCode' not in interface['CloudTrailEvent']:
                    interface_id = resource_id['ResourceName']
                elif attachment_id in self.delete_attachment_id:
                    self.delete_attachment_id.remove(attachment_id)
                if resource_id['ResourceType'] == 'AWS::EC2::Instance' and resource_id['ResourceName'] not in self.ec2_create:
                    arn_id = 'arn:aws:ec2:' + deep_get(interface, ['CloudTrailEvent', 'awsRegion']) + ':' + \
                            context().args.accountId + ':instance/' + resource_id['ResourceName']
                    if arn_id not in self.asset_delete:
                        flag = True
            if flag and interface_id:
                self.interface_create_id.add(interface_id)
        if self.interface_create_id:
            for interface_id in self.interface_create_id:
                try:
                    interface_response = context().asset_server.get_network_interface([interface_id])
                    if interface_response:
                        for network_data in interface_response['NetworkInterfaces']:
                            resource_id = 'arn:aws:ec2:' + network_data['AvailabilityZone'][:-1] + ':' + \
                                        context().args.accountId + ':instance/' + deep_get(network_data,
                                                                                    ['Attachment', 'InstanceId'])
                            interface_response['ResourceId'] = resource_id
                        interface_data = self.network_interface_process(interface_response)
                        interface_create_data.append(interface_data)
                except Exception as ex:
                    logger.debug("Failed to fetch %s", ex)
                    continue
        return interface_create_data


    def network_interface_delete(self):
        """Collecting Secondary Network Interface Delete attachment id"""
        # Collecting Secondary Network Interface Delete attachment id
        interface_log = context().asset_server.event_logs('DetachNetworkInterface', 'EventName')
        for interface in interface_log:
            interface['CloudTrailEvent'] = json.loads(interface['CloudTrailEvent'])
            if not deep_get(interface, ['CloudTrailEvent', 'errorCode']):
                attachment_id = deep_get(interface, ['CloudTrailEvent', 'requestParameters', 'attachmentId'])
                self.delete_attachment_id.add(attachment_id)


    def get_attachment_data(self):
        """delete Network interface using attachment id"""
        # delete Network interface using attachment id
        for attach_id in self.delete_attachment_id:
            search_attach_ip = context().car_service.graph_attribute_search('ipaddress', 'attachment_id', attach_id)
            for attach_ip in search_attach_ip:
                if deep_get(attach_ip, ["_key"]) and context().args.source in deep_get(attach_ip, ["source"]):
                    search_result = context().car_service.graph_search('ipaddress', deep_get(attach_ip, ["_key"]))
                    if search_result['result'] and search_result['related']:
                        for car_ip in search_result['related']:
                            if 'asset/' in str(deep_get(car_ip, ["node", "_id"])) and \
                                    deep_get(car_ip, ["node", "external_id"]) and context().args.source in \
                                    deep_get(car_ip, ["node", "source"]):
                                extn_id = deep_get(car_ip, ["node", "external_id"])
                                temp = dict()
                                temp['from'] = extn_id
                                temp['to'] = deep_get(attach_ip, ["_key"])
                                temp['edge_type'] = 'asset_ipaddress'
                                self.edges_update.append(temp)
            search_attach_mac = context().car_service.graph_attribute_search('macaddress', 'attachment_id', attach_id)
            for attach_mac in search_attach_mac:
                if deep_get(attach_mac, ["_key"]):
                    search_result = context().car_service.graph_search('macaddress', deep_get(attach_mac, ["_key"]))
                    if search_result['result'] and search_result['related']:
                        for car_ip in search_result['related']:
                            if 'asset/' in str(deep_get(car_ip, ["node", "_id"])) and \
                                    deep_get(car_ip, ["node", "external_id"]) and context().args.source in \
                                    deep_get(car_ip, ["node", "source"]):
                                extn_id = deep_get(car_ip, ["node", "external_id"])
                                temp = dict()
                                temp['from'] = extn_id
                                temp['to'] = deep_get(attach_mac, ["_key"])
                                temp['edge_type'] = 'asset_macaddress'
                                self.edges_update.append(temp)

            search_attach_dns = context().car_service.graph_attribute_search('hostname', 'attachment_id', attach_id)
            for attach_host in search_attach_dns:
                if deep_get(attach_host, ["_key"]):
                    search_result = context().car_service.graph_search('hostname', deep_get(attach_host, ["_key"]))
                    if search_result['result'] and search_result['related']:
                        for car_ip in search_result['related']:
                            if 'asset/' in str(deep_get(car_ip, ["node", "_id"])) and \
                                    deep_get(car_ip, ["node", "external_id"]) and context().args.source in \
                                    deep_get(car_ip, ["node", "source"]):
                                extn_id = deep_get(car_ip, ["node", "external_id"])
                                temp = dict()
                                temp['from'] = extn_id
                                temp['to'] = deep_get(attach_host, ["_key"])
                                temp['edge_type'] = 'asset_hostname'
                                self.edges_update.append(temp)

    def incremental_create_tags(self):
        """Ec2 name tag update"""
        # Ec2 name tag update
        tags_log = context().asset_server.event_logs('CreateTags', 'EventName')
        for tag in tags_log:
            instance_id, tag_value = None, None
            tag['CloudTrailEvent'] = json.loads(tag['CloudTrailEvent'])
            resource_ref = deep_get(tag, ['CloudTrailEvent', 'requestParameters', 'resourcesSet', 'items'])
            tag_ref = deep_get(tag, ['CloudTrailEvent', 'requestParameters', 'tagSet', 'items'])
            for resource_id in resource_ref:
                instance_id = resource_id['resourceId']
            for tag_name in tag_ref:
                if tag_name['key'] == 'Name':
                    tag_value = tag_name['value']
            if instance_id and tag_value and instance_id not in self.ec2_create:
                try:
                    tags_collection = context().asset_server.get_instances(instance_ids=[instance_id])
                    for instances in tags_collection:
                        for instance in instances['Instances']:
                            if deep_get(instance, ['State', 'Name']) != 'terminated':
                                resource_id = 'arn:aws:ec2:' + \
                                            instance['Placement']['AvailabilityZone'][:-1] + ':' + \
                                            context().args.accountId + ':instance/' + instance['InstanceId']
                                # instance['ResourceId'] = resource_id
                                if 'Tags' in instance:
                                    for name in instance['Tags']:
                                        if name['Key'] == 'Name':
                                            instance['name'] = name['Value']
                                updated_tag = deep_get(instance, ['name'])
                                if updated_tag:
                                    temp = dict()
                                    temp['resource_id'] = resource_id
                                    temp['name'] = updated_tag
                                    temp['resource_type'] = 'asset'
                                    self.vertices_update.append(temp)
                except Exception as ex:
                    context().logger.debug("Failed to update %s", ex)
                    continue


    def database_update_delete(self):
        """incremental Create and delete for Database"""
        update_list, delete_list, create_list = list(), list(), list()
        create_data, collection = list(), dict()
        # db create
        create_database_logs = context().asset_server.event_logs('AWS::RDS::DBInstance', 'ResourceType')
        for db_logs in create_database_logs:
            db_logs['CloudTrailEvent'] = json.loads(db_logs['CloudTrailEvent'])
            if db_logs['EventName'] in ['CreateDBInstance', 'RestoreDBInstanceFromDBSnapshot'] and \
                    'errorCode' not in db_logs['CloudTrailEvent']:
                if deep_get(db_logs, ['CloudTrailEvent', 'responseElements', 'dbiResourceId']):
                    create_list.append(deep_get(db_logs, ['CloudTrailEvent', 'responseElements', 'dbiResourceId']))
                elif deep_get(db_logs, ['CloudTrailEvent', 'requestParameters', 'dBInstanceIdentifier']):
                    try:
                        app_db_create = context().asset_server.get_db_instances(
                            instance_identifier=deep_get(db_logs, ['CloudTrailEvent', 'requestParameters',
                                                                'dBInstanceIdentifier']))
                        for item in app_db_create:
                            create_list.append(item['DbiResourceId'])
                    except Exception as ex:
                        context().logger.debug("Not able to Found %s", ex)
                        continue
            elif db_logs['EventName'] == 'DeleteDBInstance' and 'errorCode' not in db_logs['CloudTrailEvent']:
                if deep_get(db_logs, ['CloudTrailEvent', 'responseElements', 'dbiResourceId']):
                    delete_list.append(deep_get(db_logs, ['CloudTrailEvent', 'responseElements', 'dbiResourceId']))
            elif db_logs['EventName'] == 'ModifyDBInstance' and 'errorCode' not in db_logs['CloudTrailEvent']:
                if deep_get(db_logs, ['CloudTrailEvent', 'responseElements', 'dbiResourceId']):
                    update_list.append(deep_get(db_logs, ['CloudTrailEvent', 'responseElements', 'dbiResourceId']))

        # last_run sync up
        search_data = context().car_service.graph_attribute_search('database', 'pending_update', 'active')
        if search_data:
            for item in search_data:
                if context().args.source in item['source']:
                    resource_id = item['external_id']
                    update_list.append(resource_id)

        # filter
        create_db = [create for create in create_list if create not in delete_list]
        delete_db = [delete for delete in delete_list if delete not in create_list]
        modify_db = [modify for modify in update_list if modify not in create_list and modify not in delete_list]

        # modify later and modify now
        if modify_db:
            modify_data = self.database_update(modify_db, create_data)
            collection['modify'] = modify_data

        # check for delete list from car side
        if delete_db:
            self.database_delete.extend(delete_db)
            for delete_resource in delete_list:
                resource_details = context().car_service.graph_search('database', delete_resource, context().args.source)
                if resource_details['result'] and resource_details['related']:
                    for resource_item in resource_details['related']:
                        if 'asset/' in str(deep_get(resource_item, ["node", "_id"])) and \
                                deep_get(resource_item, ["node", "external_id"]) and context().args.source in \
                                deep_get(resource_item, ["node", "source"]):
                            delete_id = deep_get(resource_item, ["node", "external_id"])
                            self.asset_delete.append(delete_id)
        # incremental create
        if create_db:
            response = context().asset_server.get_db_instances(resource_ids=create_db)
            for values in response:
                create_data.append(values)
            collection['create'] = create_data

        return collection


    def database_update(self, modify_db, create_data):
        modify_data = list()
        resource_collection = context().asset_server.get_db_instances(resource_ids=modify_db)
        for resource in resource_collection:
            resource_details = context().car_service.graph_search('database', resource['DbiResourceId'], context().args.source)
            if resource_details['result'] and resource_details['related']:
                dest_id = list()
                for resource_item in resource_details['related']:
                    if 'asset/' in str(deep_get(resource_item, ["node", "_id"])) and \
                                    deep_get(resource_item, ["node", "external_id"]) and context().args.source in \
                                    deep_get(resource_item, ["node", "source"]):
                        extn_id = deep_get(resource_item, ["node", "external_id"])
                        dest_id.append(extn_id)
                if resource['DBInstanceArn'] not in dest_id:
                    # patch call db name
                    modify_data.append(resource)
                    temp_rename = dict()
                    temp_rename['resource_id'] = resource['DbiResourceId']
                    temp_rename['resource_type'] = 'database'
                    temp_rename['name'] = resource['DBInstanceIdentifier']
                    self.vertices_update.append(temp_rename)
                elif resource['DBInstanceArn'] in dest_id:
                    dest_id.remove(resource['DBInstanceArn'])
                self.asset_delete.extend(dest_id)

                if deep_get(resource, ['PendingModifiedValues', 'DBInstanceIdentifier']):
                    temp = dict()
                    temp['resource_id'] = resource['DbiResourceId']
                    temp['resource_type'] = 'database'
                    temp['pending_update'] = 'active'
                    self.vertices_update.append(temp)
                else:
                    temp = dict()
                    temp['resource_id'] = resource['DbiResourceId']
                    temp['resource_type'] = 'database'
                    temp['pending_update'] = 'inactive'
                    self.vertices_update.append(temp)
            else:
                create_data.append(resource)
        return modify_data


    def application_update(self, create_app_name):
        """Application environment delete"""
        delete_app_name = list()

        app_data = context().asset_server.event_logs('DeleteApplication', 'EventName')
        for app_log in app_data:
            app_log['CloudTrailEvent'] = json.loads(app_log['CloudTrailEvent'])
            if deep_get(app_log, ['CloudTrailEvent', 'errorCode']) is None:
                delete_id = deep_get(app_log, ['CloudTrailEvent', 'requestParameters', 'applicationName'])
                delete_app_name.append(delete_id)

        app_update = context().asset_server.event_logs('CreateApplication', 'EventName')
        for update in app_update:
            update['CloudTrailEvent'] = json.loads(update['CloudTrailEvent'])
            if deep_get(update, ['CloudTrailEvent', 'requestParameters', 'applicationName']) \
                    and deep_get(update, ['CloudTrailEvent', 'errorCode']) is None:
                if deep_get(update, ['CloudTrailEvent', 'requestParameters', 'applicationName']) not in delete_app_name:
                    create_app_name.append(deep_get(update, ['CloudTrailEvent', 'requestParameters', 'applicationName']))
                elif deep_get(update, ['CloudTrailEvent', 'requestParameters', 'applicationName']) in delete_app_name:
                    delete_app_name.remove(deep_get(update, ['CloudTrailEvent', 'requestParameters', 'applicationName']))

        for del_id in delete_app_name:
            search_app = context().car_service.graph_attribute_search('application', 'name', del_id)
            if search_app:
                for extn_id in search_app:
                    delete_id = deep_get(extn_id, ["external_id"])
                    self.app_delete.append(delete_id)


    def application_swap_host(self):
        """Application hostname update"""
        swap_id, update_app_host = list(), list()
        swap_host_log = context().asset_server.event_logs('SwapEnvironmentCNAMEs', 'EventName')
        for swap_host in swap_host_log:
            swap_host['CloudTrailEvent'] = json.loads(swap_host['CloudTrailEvent'])
            if deep_get(swap_host, ['CloudTrailEvent', 'errorCode']) is None:
                swap_env_1 = deep_get(swap_host, ['CloudTrailEvent', 'requestParameters', 'sourceEnvironmentId'])
                swap_env_2 = deep_get(swap_host, ['CloudTrailEvent', 'requestParameters', 'destinationEnvironmentId'])
                if swap_env_1:
                    swap_id.append(swap_env_1)
                if swap_env_2:
                    swap_id.append(swap_env_2)
        if swap_id:
            env_data = context().asset_server.list_applications_env(env_id=swap_id)
            for env in env_data['Environments']:
                search_result = context().car_service.graph_attribute_search('asset', 'environment_id', env['EnvironmentId'])
                if search_result:
                    for car_host in search_result:
                        if context().args.source in deep_get(car_host, ['source']) and deep_get(car_host, ['external_id']):
                            extn_id = deep_get(car_host, ['external_id'])
                            search = context().car_service.graph_search('asset', extn_id, context().args.source)
                            if search['result'] and search['related']:
                                flag = False
                                for host in search['related']:
                                    if 'hostname/' in str(deep_get(host, ["node", "_id"])) and \
                                            deep_get(host, ["node", "resource_type"]) == 'elasticbeanstalk' and \
                                            context().args.source in deep_get(host, ["link", "source"]):
                                        if deep_get(host, ["node", "_key"]) != env['CNAME']:
                                            flag = True
                                            temp, temp_creation = dict(), dict()
                                            temp['from'] = extn_id
                                            temp['to'] = deep_get(host, ["node", "_key"])
                                            temp['edge_type'] = 'asset_hostname'
                                            self.edges_update.append(temp)
                                            temp_creation['ResourceId'] = extn_id
                                            temp_creation['networkData'] = list()
                                            temp_creation['networkData'].append({'env_host': env['CNAME']})
                                            update_app_host.append(temp_creation)
                                if flag is False:
                                    temp_creation = dict()
                                    temp_creation['ResourceId'] = extn_id
                                    temp_creation['networkData'] = list()
                                    temp_creation['networkData'].append({'env_host': env['CNAME']})
                                    update_app_host.append(temp_creation)

        return update_app_host


    def container_update_delete(self):
        """Container update logic"""
        task_list, container_create = list(), list()
        # container delete via StopTask cloud trail event log
        delete_container_logs = context().asset_server.event_logs('StopTask', 'EventName')
        for stop_task_log in delete_container_logs:
            cloud_trail_event = json.loads(stop_task_log['CloudTrailEvent'])
            if deep_get(cloud_trail_event, ['errorCode']) is None:
                task = deep_get(cloud_trail_event, ['responseElements', 'task'])
                task_arn = deep_get(task, ['taskArn'])
                task_list.append(task_arn)
                container_list = task['containers']
                for container in container_list:
                    container_arn = container['containerArn']
                    if container_arn not in self.container_delete:
                        self.container_delete.append(container_arn)

        # container delete via DeregisterInstance cloud trail event log
        delete_container_logs = context().asset_server.event_logs('DeregisterInstance', 'EventName')
        for deregister_instance_log in delete_container_logs:
            cloud_trail_event = json.loads(deregister_instance_log['CloudTrailEvent'])
            if deep_get(cloud_trail_event, ['errorCode']) is None:
                task_id = deep_get(cloud_trail_event, ['requestParameters', 'instanceId'])
                task_arn = 'arn:aws:ecs:' + cloud_trail_event['awsRegion'] + ':' + \
                        context().args.accountId + ':task/' + task_id
                task_list.append(task_arn)
                # custom attribute search is not working as expected, so the below code is based on assumption
                container_list = context().car_service.graph_attribute_search('container', 'task_id', task_arn)
                for container in container_list:
                    if context().args.source in deep_get(container, ['source']) and deep_get(container, ['external_id']):
                        container_arn_list = deep_get(container, ['external_id'])
                        for container_arn in container_arn_list:
                            if container_arn not in self.container_delete:
                                self.container_delete.append(container_arn)

        # container delete via DeleteCluster cloud trail event log
        delete_container_logs = context().asset_server.event_logs('DeleteCluster', 'EventName')
        for deregister_instance_log in delete_container_logs:
            cloud_trail_event = json.loads(deregister_instance_log['CloudTrailEvent'])
            if deep_get(cloud_trail_event, ['errorCode']) is None:
                running_tasks_count = deep_get(cloud_trail_event, ['responseElements', 'cluster', 'runningTasksCount'])
                if running_tasks_count == 0:
                    cluster_arn = deep_get(cloud_trail_event, ['responseElements', 'cluster', 'clusterArn'])
                    # custom attribute search is not working as expected, so the below code is based on assumption
                    container_list = context().car_service.graph_attribute_search('container', 'cluster_id', cluster_arn)
                    for container in container_list:
                        if context().args.source in deep_get(container, ['source']) and deep_get(container, ['external_id']):
                            task_arn = deep_get(container, ['task_id'])
                            task_list.append(task_arn)
                            container_arn_list = deep_get(container, ['external_id'])
                            for container_arn in container_arn_list:
                                if container_arn not in self.container_delete:
                                    self.container_delete.append(container_arn)

        # container create via RunTask cloud trail event
        create_container_logs = context().asset_server.event_logs('RunTask', 'EventName')
        for run_task_log in create_container_logs:
            cloud_trail_event = json.loads(run_task_log['CloudTrailEvent'])
            if deep_get(cloud_trail_event, ['errorCode']) is None:
                tasks = deep_get(cloud_trail_event, ['responseElements', 'tasks'])
                for task in tasks:
                    task_arn = task['taskArn']
                    if task_arn not in task_list:
                        cluster_arn = task['clusterArn']
                        task_detail = context().asset_server.list_running_containers(cluster_arn, task_arn)
                        for each_task in task_detail['tasks']:
                            if each_task['lastStatus'] == 'RUNNING' and each_task['launchType'] == 'EC2':
                                response = self.process_task_container(each_task)
                                container_create.append(response)

        # container create via RegisterInstance cloud trail event
        create_container_logs = context().asset_server.event_logs('RegisterInstance', 'EventName')
        for register_instance_log in create_container_logs:
            cloud_trail_event = json.loads(register_instance_log['CloudTrailEvent'])
            if deep_get(cloud_trail_event, ['errorCode']) is None:
                task_id = deep_get(cloud_trail_event, ['requestParameters', 'instanceId'])
                task_arn = 'arn:aws:ecs:' + cloud_trail_event['awsRegion'] + ':' + \
                        context().args.accountId + ':task/' + task_id
                if task_arn not in task_list:
                    cluster_arn = deep_get(cloud_trail_event, ['requestParameters', 'attributes', 'ECS_CLUSTER_NAME'])
                    task_detail = context().asset_server.list_running_containers(cluster_arn, task_arn)
                    for each_task in task_detail['tasks']:
                        if each_task['lastStatus'] == 'RUNNING' and each_task['launchType'] == 'EC2':
                            response = self.process_task_container(each_task)
                            container_create.append(response)
        return container_create


    def process_task_container(self, task):
        """Container instance id"""
        cluster_arn = task['clusterArn']
        container_instance = context().asset_server.container_ec2_instance(cluster_arn=cluster_arn,
                                                                    container_instance_arn=task['containerInstanceArn'])
        ec2_instance_id = container_instance['containerInstances'][0]['ec2InstanceId']
        describe_ec2_instance = context().asset_server.get_instances(instance_ids=[ec2_instance_id])
        for reservation in describe_ec2_instance:
            for instance_detail in reservation['Instances']:
                task['ec2InstanceId'] = 'arn:aws:ec2:' + instance_detail['Placement']['AvailabilityZone'][: -1] \
                                        + ':' + context().args.accountId + ':instance/' + instance_detail['InstanceId']
        return task


    def update_vertices(self):
        context().logger.info('Updating vertices')
        for tag in self.vertices_update:
            context().car_service.database_patch_value(tag)
        context().logger.info('Updating vertices done: %s', len(self.vertices_update))


    def update_edges(self):
        context().logger.info('Disabling edges')
        for edge in self.edges_update:
            if 'last_modified' in edge:
                context().car_service.edge_patch(context().args.source, edge, {"last_modified": edge['last_modified']})
            else:
                context().car_service.edge_patch(context().args.source, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.edges_update))


    def delete_vertices(self):
        """Summary: Delete the vertices."""
        context().logger.info('Deleting vertices')
        if self.asset_delete:
            context().car_service.delete('asset', self.asset_delete)
        if self.ip_delete:
            context().car_service.delete('ipaddress', self.ip_delete)
        if self.dns_delete:
            context().car_service.delete('hostname', self.dns_delete)
        if self.vuln_delete:
            context().car_service.delete('vulnerability', self.vuln_delete)
        if self.app_delete:
            context().car_service.delete('application', self.app_delete)
        if self.database_delete:
            context().car_service.delete('database', self.database_delete)
        if self.container_delete:
            context().car_service.delete('container', self.container_delete)
        context().logger.info('Deleting vertices done: %s', {
            'asset': len(self.asset_delete),
            'ipaddress': len(self.ip_delete),
            'hostname': len(self.dns_delete),
            'vulnerability': len(self.vuln_delete),
            'application': len(self.app_delete),
            'database': len(self.database_delete),
            'container': len(self.container_delete)
        } )