import datetime, re
from car_framework.context import context
from connector.data_collector import deep_get

EBS_ENV_ID_TAG = 'elasticbeanstalk:environment-id'
EBS_ENV_NAME_TAG = 'elasticbeanstalk:environment-name'


def get_report_time():
    delta = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


class DataHandler(object):
    source = None
    report = None

    def __init__(self):
        self.collections = {}
        self.collection_keys = {}
        self.edges = {}
        self.edge_keys = {}
        self.timestamp = get_report_time()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry and it is compuslory for each imports API call
            self.source = {'_key': context().args.source, 'name': context().args.accountId, 'description': 'AWS cloud datasource'}
            self.report = {'_key': str(self.timestamp), 'timestamp': self.timestamp, 'type': 'AWS cloud datasource',
                           'description': 'AWS cloud datasource'}

        return {'source': self.source, 'report': self.report}

    # Adds the collection data
    def add_collection(self, name, object, key):
        objects = self.collections.get(name)
        if not objects:
            objects = [];
            self.collections[name] = objects

        keys = self.collection_keys.get(name)
        if not keys:
            keys = [];
            self.collection_keys[name] = keys

        # Remove "/" from values since it will split the string on CAR's side, which will result in edges not connecting to their vertices
        self.fix_arn(object)

        if not object[key] in self.collection_keys[name]:
            objects.append(object)
            self.collection_keys[name].append(object[key])

    # Adds the edge between two vertices
    def add_edge(self, name, object):
        objects = self.edges.get(name)
        if not objects:
            objects = [];
            self.edges[name] = objects

        keys = self.collection_keys.get(name)
        if not keys:
            keys = [];
            self.edge_keys[name] = keys

        # Remove "/" from values since it will split the string on CAR's side, which will result in edges not connecting to their vertices
        self.fix_arn(object)

        key = '#'.join(str(x) for x in object.values())
        if not key in self.edge_keys[name]:
            object['report'] = self.report['_key']
            object['source'] = context().args.source
            object['active'] = True
            object['timestamp'] = self.report['timestamp']
            objects.append(object)
            self.edge_keys[name].append(key)

    def fix_arn(self, obj):
        for k, v in obj.items():
            if type(v) == str and k not in ('_from', '_to'):
                obj[k] = v.replace("/", ":")
        return obj

    def handle_asset(self, obj):
        asset = dict()
        if deep_get(obj, ['ResourceId']):
            asset['external_id'] = obj['ResourceId']
            asset['name'] = 'EC2 id:' + obj['InstanceId']
            if 'Tags' in obj:
                for name in obj['Tags']:
                    if deep_get(name, ['Key']) == 'Name':
                        asset['name'] = name['Value']
                    if deep_get(name, ['Key']) == EBS_ENV_ID_TAG:
                        asset['environment_id'] = name['Value']
        elif deep_get(obj, ['DBInstanceArn']):
            asset_id = deep_get(obj, ["DBInstanceArn"])
            asset['external_id'] = asset_id
            asset['name'] = deep_get(obj, ["DBInstanceIdentifier"])
            # asset['engine'] = deep_get(obj, ["Engine"])

        if asset: self.add_collection('asset', asset, 'external_id')

    def handle_geolocation(self, obj):
        geolocation = dict()
        # commented for including App related - EC2s
        if deep_get(obj, ['ResourceId']):
            location = deep_get(obj, ['Placement', 'AvailabilityZone'])[:-1]
            geolocation['external_id'] = location
            geolocation['region'] = location
        elif deep_get(obj, ['DBInstanceArn']):
            location = deep_get(obj, ['AvailabilityZone'])[:-1]
            geolocation['external_id'] = location
            geolocation['region'] = location

        if geolocation: self.add_collection('geolocation', geolocation, 'external_id')

    def handle_ipaddress(self, obj):
        # Handle assets/db/etc. network data
        if deep_get(obj, ['networkData']):
            for interfaces in obj['networkData']:
                if deep_get(interfaces, ['IpAddress']):
                    for ip_value in interfaces['IpAddress']:
                        ipaddress = dict()
                        ipaddress['_key'] = ip_value
                        ipaddress['network_interface_id'] = interfaces['NetworkInterfaceId']
                        ipaddress['attachment_id'] = interfaces['AttachmentId']
                        self.add_collection('ipaddress', ipaddress, '_key')
        # Handle actual user network data
        if 'UserSourceIpAddress' in obj and obj['UserSourceIpAddress']:
            user_ipaddress = dict()
            user_ipaddress['_key'] = obj['UserSourceIpAddress']
            self.add_collection('ipaddress', user_ipaddress, '_key')

    def handle_macaddress(self, obj):
        if deep_get(obj, ['networkData']):
            for interfaces in obj['networkData']:
                mac_address = deep_get(interfaces, ['MacAddress'])
                if mac_address:
                    macaddress = dict()
                    macaddress['_key'] = mac_address
                    macaddress['network_interface_id'] = deep_get(interfaces, ['NetworkInterfaceId'])
                    macaddress['attachment_id'] = deep_get(interfaces, ['AttachmentId'])
                    self.add_collection('macaddress', macaddress, '_key')

    def handle_hostname(self, obj):
        if deep_get(obj, ['networkData']):
            for interfaces in obj['networkData']:
                if deep_get(interfaces, ['DnsName']):
                    for host in interfaces['DnsName']:
                        if host:
                            hostname = dict()
                            hostname['_key'] = host
                            hostname['network_interface_id'] = deep_get(interfaces, ['NetworkInterfaceId'])
                            hostname['attachment_id'] = interfaces['AttachmentId']
                            self.add_collection('hostname', hostname, '_key')
                elif deep_get(interfaces, ['env_host']):
                    host = deep_get(interfaces, ['env_host'])
                    if host:
                        hostname = dict()
                        hostname['_key'] = host
                        hostname['resource_type'] = 'elasticbeanstalk'
                        self.add_collection('hostname', hostname, '_key')

        elif deep_get(obj, ['DBInstanceArn']):
            host = deep_get(obj, ["Endpoint", "Address"])
            if host:
                hostname = dict()
                hostname['_key'] = host
                self.add_collection('hostname', hostname, '_key')

    def handle_vulnerability(self, obj):
        vulnerability = dict()
        vulnerability['external_id'] = obj['Id']
        vulnerability['name'] = obj['Title']
        vulnerability['description'] = obj['Description']
        vulnerability['disclosed_on'] = obj.get('FirstObservedAt')
        vulnerability['published_on'] = obj['CreatedAt']
        vulnerability['base_score'] = round(int(deep_get(obj, ['Severity', 'Normalized'])) / 10)
        self.add_collection('vulnerability', vulnerability, 'external_id')

    def handle_application(self, obj):
        application = dict()

        if deep_get(obj, ['ApplicationName']):
            application['name'] = obj['ApplicationName']
            application['description'] = "App name is " + obj['ApplicationName']
            application['external_id'] = obj['ApplicationArn']

        elif deep_get(obj, ['ImageId']):
            application['name'] = obj['ImageName']
            application['is_os'] = True
            application['external_id'] = obj['ImageId']

        elif deep_get(obj, ['Engine']):
            application['name'] = deep_get(obj, ['Engine'])
            application['external_id'] = deep_get(obj, ['Engine'])

        if application: self.add_collection('application', application, 'external_id')

    def handle_database(self, obj):
        database = dict()
        # database_id = deep_get(obj, ["DBInstanceArn"])
        if obj["DbiResourceId"]:
            database['name'] = deep_get(obj, ["DBInstanceIdentifier"])
            database['external_id'] = deep_get(obj, ["DbiResourceId"])
            if deep_get(obj, ['PendingModifiedValues', 'DBInstanceIdentifier']):
                database['pending_update'] = 'active'
            else:
                database['pending_update'] = 'inactive'

            self.add_collection('database', database, 'external_id')

    def handle_user(self, obj):
        user = dict()
        if 'Username' in obj and obj['Username'] and obj['Username'].lower() != 'autoscaling':
            user['external_id'] = obj['Username']
            user['username'] = obj['Username']
            if 'SourceUserAgent' in obj:
                user['source_user_agent'] = obj['SourceUserAgent']
            self.add_collection('user', user, 'external_id')
        elif deep_get(obj, ['DBInstanceArn']):
            user['external_id'] = obj['MasterUsername']
            user['username'] = obj['MasterUsername']
            user['role'] = 'TECHNICAL OWNER'
            self.add_collection('user', user, 'external_id')

    def handle_account(self, obj):
        account = dict()
        if 'Username' in obj and obj['Username'] and obj['Username'].lower() != 'autoscaling':
            account['external_id'] = obj['Username']
            account['name'] = obj['Username']
            if 'SourceUserAgent' in obj:
                account['source_user_agent'] = obj['SourceUserAgent']
            self.add_collection('account', account, 'external_id')
        elif deep_get(obj, ['DBInstanceArn']):
            account['external_id'] = obj['MasterUsername']
            account['name'] = obj['MasterUsername']
            self.add_collection('account', account, 'external_id')

    def handle_container(self, obj):
        container = dict()
        if deep_get(obj, ["containers"]):
            for item in deep_get(obj, ["containers"]):
                container['external_id'] = item["containerArn"]
                container['name'] = item["name"]
                container['image'] = item["image"]
                container['task_id'] = item["taskArn"]
                container['cluster_id'] = obj["clusterArn"]
                self.add_collection('container', container, 'external_id')

    def handle_ipaddress_macaddress(self, obj):
        if deep_get(obj, ['networkData']):
            for interfaces in obj['networkData']:
                if deep_get(interfaces, ['MacAddress']) and deep_get(interfaces, ['IpAddress']):
                    mac_address = deep_get(interfaces, ['MacAddress'])
                    for ip_value in interfaces['IpAddress']:
                        ipaddress_macaddress = dict()
                        ipaddress_macaddress['_from'] = 'ipaddress/' + ip_value
                        ipaddress_macaddress['_to'] = 'macaddress/' + mac_address
                        self.add_edge('ipaddress_macaddress', ipaddress_macaddress)

    def handle_asset_ipaddress(self, obj):
        if deep_get(obj, ['networkData']):
            for interfaces in obj['networkData']:
                if deep_get(interfaces, ['IpAddress']):
                    for ip_value in interfaces['IpAddress']:
                        asset_ipaddress = dict()
                        asset_ipaddress['_from_external_id'] = obj['ResourceId']
                        asset_ipaddress['_to'] = 'ipaddress/' + ip_value
                        self.add_edge('asset_ipaddress', asset_ipaddress)
        if 'UserSourceIpAddress' in obj and obj['UserSourceIpAddress']:
            asset_user_ipaddress = dict()
            asset_user_ipaddress['_from_external_id'] = obj['ResourceId']
            asset_user_ipaddress['_to'] = 'ipaddress/' + obj['UserSourceIpAddress']
            self.add_edge('asset_ipaddress', asset_user_ipaddress)

    def handle_asset_macaddress(self, obj):
        if deep_get(obj, ['networkData']):
            for interfaces in obj['networkData']:
                mac_address = deep_get(interfaces, ['MacAddress'])
                if mac_address:
                    asset_macaddress = dict()
                    asset_macaddress['_from_external_id'] = obj['ResourceId']
                    asset_macaddress['_to'] = 'macaddress/' + mac_address
                    self.add_edge('asset_macaddress', asset_macaddress)

    def handle_asset_hostname(self, obj):
        if deep_get(obj, ['networkData']):
            for interfaces in obj['networkData']:
                if deep_get(interfaces, ['DnsName']):
                    for host in interfaces['DnsName']:
                        asset_hostname = dict()
                        asset_hostname['_from_external_id'] = obj['ResourceId']
                        asset_hostname['_to'] = 'hostname/' + host
                        self.add_edge('asset_hostname', asset_hostname)

                elif deep_get(interfaces, ['env_host']):
                    asset_hostname = dict()
                    asset_hostname['_from_external_id'] = obj['ResourceId']
                    asset_hostname['_to'] = 'hostname/' + deep_get(interfaces, ['env_host'])
                    self.add_edge('asset_hostname', asset_hostname)

        elif deep_get(obj, ['DBInstanceArn']):
            asset_id = deep_get(obj, ["DBInstanceArn"])
            asset_hostname = dict()
            asset_hostname['_from_external_id'] = asset_id
            asset_hostname['_to'] = 'hostname/' + deep_get(obj, ["Endpoint", "Address"])
            self.add_edge('asset_hostname', asset_hostname)

    def handle_asset_vulnerability(self, obj):
        asset_vulnerability = dict()
        asset_vulnerability['_from_external_id'] = obj['Resources'][0]['Id']
        asset_vulnerability['_to_external_id'] = obj['Id']
        self.add_edge('asset_vulnerability', asset_vulnerability)

    def handle_asset_application(self, obj):
        asset_application = dict()
        if deep_get(obj, ['ApplicationArn']):
            asset_application['_from_external_id'] = deep_get(obj, ['ResourceId'])
            asset_application['_to_external_id'] = deep_get(obj, ['ApplicationArn'])
        elif deep_get(obj, ['ImageId']):
            asset_application['_from_external_id'] = obj['ResourceId']
            asset_application['_to_external_id'] = deep_get(obj, ['ImageId'])
        elif deep_get(obj, ['Engine']):
            asset_application['_from_external_id'] = obj['DBInstanceArn']
            asset_application['_to_external_id'] = deep_get(obj, ['Engine'])

        if asset_application: self.add_edge('asset_application', asset_application)

    def handle_asset_database(self, obj):
        asset_database = dict()
        if obj["DBInstanceArn"]:
            database_id = deep_get(obj, ["DBInstanceArn"])
            asset_database['_from_external_id'] = database_id
            asset_database['_to_external_id'] = deep_get(obj, ["DbiResourceId"])
            self.add_edge('asset_database', asset_database)

    def handle_asset_geolocation(self, obj):
        asset_geolocation = dict()
        if deep_get(obj, ['ResourceId']):
            asset_geolocation['_from_external_id'] = obj['ResourceId']
            asset_geolocation['_to_external_id'] = deep_get(obj, ['Placement', 'AvailabilityZone'])[:-1]
        elif obj["DBInstanceArn"]:
            asset_geolocation['_from_external_id'] = deep_get(obj, ["DBInstanceArn"])
            asset_geolocation['_to_external_id'] = deep_get(obj, ["AvailabilityZone"])[:-1]

        if asset_geolocation: self.add_edge('asset_geolocation', asset_geolocation)

    def handle_user_account(self, obj):
        user_account = dict()
        if 'Username' in obj and obj['Username'] and obj['Username'].lower() != 'autoscaling':
            user_account['_from_external_id'] = obj['Username']
            user_account['_to_external_id'] = obj['Username']
            self.add_edge('user_account', user_account)
        elif deep_get(obj, ['DBInstanceArn']):
            # resource_id = deep_get(obj, ['DbiResourceId'])
            user_account['_from_external_id'] = deep_get(obj, ['MasterUsername'])
            user_account['_to_external_id'] = deep_get(obj, ['MasterUsername'])
            self.add_edge('user_account', user_account)

    def handle_account_database(self, obj):
        account_database = dict()
        if 'Username' in obj and obj['Username'] and obj['Username'].lower() != 'autoscaling' and deep_get(obj, ['DBInstanceArn']):
            account_database['_from_external_id'] = obj['Username']
            account_database['_to_external_id'] = deep_get(obj, ['DbiResourceId'])
            self.add_edge('account_database', account_database)
        elif deep_get(obj, ['DBInstanceArn']):
            account_database['_from_external_id'] = deep_get(obj, ['MasterUsername'])
            account_database['_to_external_id'] = deep_get(obj, ['DbiResourceId'])
            self.add_edge('account_database', account_database)

    def handle_asset_container(self, obj):
        if deep_get(obj, ["containers"]):
            for item in deep_get(obj, ["containers"]):
                asset_container = dict()
                asset_container['_from_external_id'] = obj['ec2InstanceId']
                asset_container['_to_external_id'] = item["containerArn"]
                self.add_edge('asset_container', asset_container)

    def handle_ipaddress_container(self, obj):
        if deep_get(obj, ["containers"]):
            for item in deep_get(obj, ["containers"]):
                network_interface = item.get('networkInterfaces')
                if network_interface:
                    ipaddress_container = dict()
                    ipaddress_container['_from'] = 'ipaddress/' + network_interface[0]['privateIpv4Address']
                    ipaddress_container['_to_external_id'] = item["containerArn"]
                    self.add_edge('ipaddress_container', ipaddress_container)

    def handle_account_ipaddress(self, obj):
        if 'Username' in obj and obj['Username'] and obj['UserSourceIpAddress']:
            account_ipaddress = dict()
            account_ipaddress['_from_external_id'] = obj['Username']
            account_ipaddress['_to'] = 'ipaddress/' + obj['UserSourceIpAddress']
            self.add_edge('account_ipaddress', account_ipaddress)

    def handle_account_application(self, obj):
        if 'Username' in obj and obj['Username'] and obj['Username'].lower() != 'autoscaling':
            account_application = dict()
            account_application['_from_external_id'] = obj['Username']

            if deep_get(obj, ['ApplicationArn']):
                account_application['_to_external_id'] = deep_get(obj, ['ApplicationArn'])
            elif deep_get(obj, ['ImageId']):
                account_application['_to_external_id'] = deep_get(obj, ['ImageId'])
            elif deep_get(obj, ['Engine']):
                account_application['_to_external_id'] = deep_get(obj, ['Engine'])
            if '_to_external_id' in account_application.keys():
                self.add_edge('account_application', account_application)

    def handle_asset_account(self, obj):
        if 'Username' in obj and obj['Username'] and obj['Username'].lower() != 'autoscaling':
            asset_account = dict()
            asset_account['_from_external_id'] = obj['ResourceId']
            asset_account['_to_external_id'] = obj['Username']
            self.add_edge('asset_account', asset_account)

    def handle_database_ipaddress(self, obj):
        if 'UserSourceIpAddress' in obj and obj['UserSourceIpAddress'] and deep_get(obj, ['DBInstanceArn']):
            database_ipaddress = dict()
            database_ipaddress['_from_external_id'] = deep_get(obj, ['DbiResourceId'])
            database_ipaddress['_to'] = 'ipaddress/' + obj['UserSourceIpAddress']
            self.add_edge('database_ipaddress', database_ipaddress)

    def handle_application_ipaddress(self, obj):
        if 'UserSourceIpAddress' in obj and obj['UserSourceIpAddress']:
            application_ipaddress = dict()
            if deep_get(obj, ['ApplicationArn']):
                application_ipaddress['_from_external_id'] = deep_get(obj, ['ApplicationArn'])
                application_ipaddress['_to'] = 'ipaddress/' + obj['UserSourceIpAddress']
            elif deep_get(obj, ['ImageId']):
                application_ipaddress['_from_external_id'] = deep_get(obj, ['ImageId'])
                application_ipaddress['_to'] = 'ipaddress/' + obj['UserSourceIpAddress']
            elif deep_get(obj, ['Engine']):
                application_ipaddress['_from_external_id'] = deep_get(obj, ['Engine'])
                application_ipaddress['_to'] = 'ipaddress/' + obj['UserSourceIpAddress']

            if application_ipaddress:
                self.add_edge('application_ipaddress', application_ipaddress)

    def handle_ipaddress_vulnerability(self, obj):
        if 'UserSourceIpAddress' in obj and obj['UserSourceIpAddress']:
            ipaddress_vulnerability = dict()
            ipaddress_vulnerability['_from_external_id'] = obj['UserSourceIpAddress']
            ipaddress_vulnerability['_to_external_id'] = obj['Id']
            self.add_edge('ipaddress_vulnerability', ipaddress_vulnerability)

    def printData(self):
        context().logger.debug("Vertexes to be created:")
        context().logger.debug(self.collections)
        context().logger.debug("Edges to be created:")
        context().logger.debug(self.edges)