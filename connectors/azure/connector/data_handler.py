import datetime, re
from car_framework.context import context
from connector.data_collector import deep_get, timestamp_conv

RESOURCE_LIST = ["Virtual Machine", "App Service", "SQL Database"]
BASE_SCORE_MAP = {"high": 8, "medium": 5, "low": 2}

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
            self.source = {'_key': context().args.source, 'name': context().args.tenantID, 'description': 'Microsoft Azure imports'}
            self.report = {'_key': str(self.timestamp), 'timestamp' : self.timestamp, 'type': 'MS Azure', 'description': 'Microsoft Azure imports'}
        
        return {'source': self.source, 'report': self.report}

    # Adds the collection data
    def add_collection(self, name, object, key):
        objects = self.collections.get(name)
        if not objects:
            objects = []; self.collections[name] = objects
        
        keys = self.collection_keys.get(name)
        if not keys:
            keys = []; self.collection_keys[name] = keys
        
        if not object[key] in self.collection_keys[name]:
            objects.append(object)
            self.collection_keys[name].append(object[key])

    # Adds the edge between two vertices
    def add_edge(self, name, object):
        objects = self.edges.get(name)
        if not objects:
            objects = []; self.edges[name] = objects

        keys = self.collection_keys.get(name)
        if not keys:
            keys = []; self.edge_keys[name] = keys
        
        key = '#'.join(str(x) for x in object.values())
        if not key in self.edge_keys[name]:
            object['report'] = self.report['_key']
            object['source'] = context().args.source
            object['active'] = True
            object['timestamp'] = self.report['timestamp']
            objects.append(object)
            self.edge_keys[name].append(key)

    def handle_asset(self, obj):
        asset = dict()
        if "vm_map" in obj:
            asset['external_id'] = (obj['vm_map']['id']).lower()
            asset['name'] = obj['vm_map']['name']
            asset["description"] = "VM Image details: " \
                                   + deep_get(obj, ["vm_map", "properties", "storageProfile", "imageReference",
                                                    "offer"]) + '-' \
                                   + deep_get(obj, ["vm_map", "properties", "storageProfile", "imageReference", "sku"])
            self.add_collection('asset', asset, 'external_id')

        elif "application_map" in obj:
            asset['external_id'] = deep_get(obj, ["application_map", "id"]).lower()
            asset['name'] = deep_get(obj, ["application_map", "name"])
            asset["description"] = "App Service name is " + deep_get(obj, ["application_map", "name"]) + \
                                   " and provider is " + deep_get(obj, ["application_map", "type"])
            self.add_collection('asset', asset, 'external_id')

        elif "database_map" in obj:
            asset_id = deep_get(obj, ["database_map", "server_map", "id"]).lower()
            asset['external_id'] = asset_id
            asset['name'] = deep_get(obj, ["database_map", "server_map", "name"])
            asset["description"] = "SQL server name is " + deep_get(obj, ["database_map", "server_map", "name"]) + \
                                    " and location is " + deep_get(obj, ["database_map", "server_map", "location"])
            self.add_collection('asset', asset, 'external_id')

            # TODO: Needs confirmation (Azure container instances do not have vulnerability in ASC)
        # elif "container_map" in obj:
        #     asset['external_id'] = deep_get(obj, ["container_map", "id"])).lower()
        #     asset['name'] = deep_get(obj, ["container_map", "name"])
        #     asset["description"] = "Container name is " + deep_get(obj, ["container_map", "name"]) + \
        #                            " and provider is " + deep_get(obj, ["container_map", "type"])
        #     self.result.append(asset)

    def handle_ipaddress(self, obj):
        """ :param obj: dict, json response of the API calls
            :param _ipaddress: dict, empty dict
        """
        ipaddresses = deep_get(obj, ["network_map", "properties", "ipConfigurations", "properties", "IPAddress"])
        if ipaddresses:
            for ip_addr in ipaddresses:
                ipaddress = dict()
                ipaddress['_key'] = ipaddresses[ip_addr]
                self.add_collection('ipaddress', ipaddress, '_key')

        elif "application_map" in obj:
            ip_addr = deep_get(obj, ["application_map", "properties", "inboundIpAddress"])
            ipaddress = dict()
            ipaddress['_key'] = ip_addr
            self.add_collection('ipaddress', ipaddress, '_key')


    def handle_macaddress(self, obj):
        mac = deep_get(obj, ["network_map", "properties", "macAddress"])
        if mac:
            macaddress = dict()
            macaddress['_key'] = mac.replace("-", ":")
            self.add_collection('macaddress', macaddress, '_key')


    def handle_hostname(self, obj):
        if deep_get(obj, ["network_map", "properties", "ipConfigurations", "properties", "fqdn"]):
            hostname = dict()
            hostname['_key'] = deep_get(obj,
                                        ["network_map", "properties", "ipConfigurations", "properties", "fqdn"])
            hostname['description'] = "hostname of virtual machine resource"
            self.add_collection('hostname', hostname, '_key')

        elif "application_map" in obj:
            hostnames = deep_get(obj, ["application_map", "properties", "hostNames"])
            for host in hostnames:
                hostname = dict()
                hostname['_key'] = host
                hostname['description'] = "hostname of app service resource"
                self.add_collection('hostname', hostname, '_key')

        elif "database_map" in obj:
            hostname = dict()
            host = deep_get(obj, ["database_map", "server_map", "properties", "fullyQualifiedDomainName"])
            hostname['_key'] = host
            hostname['description'] = "hostname of SQL server"
            self.add_collection('hostname', hostname, '_key')


    def handle_ipaddress_macaddress(self, obj):
        ipaddresses = deep_get(obj, ["network_map", "properties", "ipConfigurations", "properties", "IPAddress"])
        mac = deep_get(obj, ["network_map", "properties", "macAddress"])
        if ipaddresses and mac:
            for ip_addr in ipaddresses:
                ipaddress_macaddress = dict()
                ipaddress_macaddress['_from'] = 'ipaddress/' + ipaddresses[ip_addr]
                ipaddress_macaddress['_to'] = 'macaddress/' + mac.replace("-", ":")
                self.add_edge('ipaddress_macaddress', ipaddress_macaddress)


    def handle_asset_ipaddress(self, obj):
        ipaddresses = deep_get(obj, ["network_map", "properties", "ipConfigurations", "properties", "IPAddress"])
        if deep_get(obj, ["network_map", "properties", "virtualMachine", "id"]) and ipaddresses:
            for ip_addr in ipaddresses:
                asset_ipaddress = dict()
                asset_ipaddress['_from_external_id'] = deep_get(obj, ["network_map", "properties", "virtualMachine", "id"]).lower()
                asset_ipaddress['_to'] = 'ipaddress/' + ipaddresses[ip_addr]
                self.add_edge('asset_ipaddress', asset_ipaddress)

        elif "application_map" in obj:
            asset_ipaddress = dict()
            asset_ipaddress['_from_external_id'] = deep_get(obj, ["application_map", "id"]).lower()
            asset_ipaddress['_to'] = 'ipaddress/' + deep_get(obj, ["application_map", "properties", "inboundIpAddress"])
            self.add_edge('asset_ipaddress', asset_ipaddress)


    def handle_asset_macaddress(self, obj):
        macaddress = deep_get(obj, ["network_map", "properties", "macAddress"])
        if deep_get(obj, ["network_map", "properties", "virtualMachine", "id"]) and macaddress:
            asset_macaddress= dict()
            asset_macaddress['_from_external_id'] = deep_get(obj, ["network_map", "properties", "virtualMachine", "id"]).lower()
            asset_macaddress['_to'] = 'macaddress/' + macaddress.replace("-", ":")
            self.add_edge('asset_macaddress', asset_macaddress)


    def handle_asset_hostname(self, obj):
        asset_hostname = dict()
        if deep_get(obj, ["network_map", "properties", "ipConfigurations", "properties", "fqdn"]) and deep_get(obj, ["network_map", "properties", "virtualMachine", "id"]):
            asset_hostname['_from_external_id'] = deep_get(obj, ["network_map", "properties", "virtualMachine", "id"]).lower()
            asset_hostname['_to'] = 'hostname/' + deep_get(obj, ["network_map", "properties", "ipConfigurations", "properties", "fqdn"])
            self.add_edge('asset_hostname', asset_hostname)

        elif "application_map" in obj:
            hostnames = deep_get(obj, ["application_map", "properties", "hostNames"])
            for host in hostnames:
                asset_hostname = dict()
                asset_hostname['_from_external_id'] = deep_get(obj, ["application_map", "id"]).lower()
                asset_hostname['_to'] = 'hostname/' + host
                self.add_edge('asset_hostname', asset_hostname)

        elif "database_map" in obj:
            asset_id = deep_get(obj, ["database_map", "server_map", "id"]).lower()
            asset_hostname['_from_external_id'] = asset_id
            asset_hostname['_to'] = 'hostname/' + deep_get(obj, ["database_map", "server_map", "properties", "fullyQualifiedDomainName"])
            self.add_edge('asset_hostname', asset_hostname)

            # TODO: Needs confirmation (Azure container instances do not have vulnerability in ASC)
        # elif "container_map" in obj:
        #     asset_hostname['_from_external_id'] = deep_get(obj, ["container_map", "id"]))
        #     asset_hostname['_to'] = 'hostname/' + deep_get(obj,
        #                                                    ["container_map", "properties", "ipAddress", "fqdn"])
        #     self.add_edge('asset_hostname', asset_hostname)


    def handle_vulnerability(self, obj):
        vulnerability = dict()

        if not context().args.switch:
            vulnerability['external_id'] = obj['name']
            vulnerability['name'] = deep_get(obj, ['properties', 'alertDisplayName'])
            vulnerability['description'] = deep_get(obj, ['properties', 'description'])
            vulnerability['disclosed_on'] = deep_get(obj, ['properties', 'detectedTimeUtc'])
            vulnerability['published_on'] = deep_get(obj, ['properties', 'reportedTimeUtc'])
            severity = deep_get(obj, ['properties', 'reportedSeverity'])
            vulnerability['base_score'] = BASE_SCORE_MAP.get(severity.lower(), 0)
        else:
            vulnerability['external_id'] = obj['eventDataId']
            vulnerability['name'] = deep_get(obj, ['eventName', 'value'])
            vulnerability['description'] = obj['description']
            vulnerability['disclosed_on'] = obj['submissionTimestamp']
            vulnerability['published_on'] = obj['eventTimestamp']
        
        self.add_collection('vulnerability', vulnerability, 'external_id')

    def handle_asset_vulnerability(self, obj):
        asset_vulnerability = dict()

        if not context().args.switch:
            associated_resource = deep_get(obj, ['properties', 'associatedResource'])
            match_flag = re.search(r"//", associated_resource)
            resource_type = deep_get(obj, ["properties", "extendedProperties", "resourceType"])

            if not match_flag and resource_type in RESOURCE_LIST:
                if resource_type == "SQL Database":
                    associated_resource = '/'.join(associated_resource.split('/')[:-2])

                asset_vulnerability['_from_external_id'] = associated_resource.lower()
                asset_vulnerability['_to_external_id'] = obj['name']
                asset_vulnerability['timestamp'] = timestamp_conv(deep_get(obj, ['properties', 'reportedTimeUtc']))
        else:
            if deep_get(obj, ['vm_map', 'id']) or deep_get(obj, ['application_map', 'id']) \
                    or deep_get(obj, ['database_map', 'id']):
                if "vm_map" in obj:
                    asset_vulnerability['_from_external_id'] = deep_get(obj, ['vm_map', 'id']).lower()
                elif "application_map" in obj:
                    asset_vulnerability['_from_external_id'] = deep_get(obj, ['application_map', 'id']).lower()
                elif "database_map" in obj:
                    asset_vulnerability['_from_external_id'] = deep_get(obj, ['database_map', 'id']).lower()
                asset_vulnerability['_to_external_id'] = obj['eventDataId']
                asset_vulnerability['timestamp'] = timestamp_conv(obj['eventTimestamp'])
        
        if asset_vulnerability:
            self.add_edge('asset_vulnerability', asset_vulnerability)


    def handle_application(self, obj):
        if obj["application_map"]:
            application = dict()
            application['name'] = deep_get(obj, ["application_map", "name"])
            description = "App name is, " + deep_get(obj, ["application_map", "name"]) + " ,provider is " + deep_get(
                obj, ["application_map", "type"]) + " and location is, " + deep_get(obj,
                                                                                    ["application_map", "location"])
            application['description'] = description
            application['external_id'] = deep_get(obj, ["application_map", "id"]).lower()
            self.add_collection('application', application, 'external_id')


    def handle_asset_application(self, obj):
        asset_application = dict()
        if obj["application_map"]:
            asset_application['_from_external_id'] = deep_get(obj, ["application_map", "id"]).lower()
            asset_application['_to_external_id'] = deep_get(obj, ["application_map", "id"]).lower()
            self.add_edge('asset_application', asset_application)


    def handle_database(self, obj):
        if obj["database_map"]:
            database = dict()
            database['name'] = deep_get(obj, ["database_map", "name"])
            database['description'] = "Database name is, " + deep_get(obj, ["database_map", "name"]) + \
                                      " ,and location is " + deep_get(obj, ["database_map", "location"])
            database['external_id'] = deep_get(obj, ["database_map", "id"]).lower()
            self.add_collection('database', database, 'external_id')


    def handle_asset_database(self, obj):
        if obj["database_map"]:
            asset_database = dict()
            asset_id = deep_get(obj, ["database_map", "server_map", "id"])
            database_id = deep_get(obj, ["database_map", "id"])
            if asset_id and database_id:
                asset_database['_from_external_id'] = asset_id.lower()
                asset_database['_to_external_id'] = database_id.lower()
                self.add_edge('asset_database', asset_database)

# TODO: Needs confirmation (Azure container instances do not have vulnerability in ASC)
# class ContainerConsumer(DataConsumer):
#     def consume(self, obj, container):
#         if obj["container_map"]:
#             container['external_id'] = deep_get(obj, ["container_map", "id"]))
#             container['name'] = deep_get(obj, ["container_map", "name"])
#             temp = deep_get(obj, ["container_map", "properties", "containers"])[0]
#             container['image'] = deep_get(temp, ["properties", "image"])
#             self.result.append(container)
#
#
# class IPAddressContainerConsumer(EdgeDataConsumer):
#     def consume(self, obj, ipaddress_container):
#         if obj["container_map"]:
#             ipaddress_container['_from'] = 'ipaddress/' + deep_get(obj, ["container_map", "properties", "ipAddress",
#                                                                          "ip"])
#             ipaddress_container['_to_external_id'] = deep_get(obj, ["container_map", "id"]))
#             self.result.append(ipaddress_container)



    def printData(self):
        context().logger.debug("Vertexes to be created:")
        context().logger.debug(self.collections)
        context().logger.debug("Edges to be created:")
        context().logger.debug(self.edges)