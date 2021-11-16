import json
from datetime import datetime

from car_framework.context import context


def deep_get(_dict, keys, default=""):
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict

def timestamp_conv(time_string):
    time_pattern = "%Y-%m-%dT%H:%M:%S"
    epoch = datetime(1970, 1, 1)
    converted_time = int(((datetime.strptime(str(time_string)[:19], time_pattern) - epoch).total_seconds()) * 1000)
    return converted_time

def convert_lower(id_string):
    return id_string.lower()
    
class DataCollector(object):

    update_edge = []
    delete_data = {
        'asset': [],
        'application': [],
        'database': [],
    }

    _collected_data = {}

    def _get_collected_data(self, data, incremental=True):
        if not self._collected_data.get(data):
            if data == 'map_data_security':
                if not context().args.switch:
                    if incremental:
                        self._collected_data[data] = context().asset_server.get_security_center_alerts(context().last_model_state_id)
                    else:
                        self._collected_data[data] = context().asset_server.get_security_center_alerts()
                else:
                    self._collected_data[data] = context().asset_server.get_security_logs(context().last_model_state_id)
            elif data == 'map_all_vmachine':
                self._collected_data[data] = context().asset_server.get_virtual_machine_details(resource_id=None, incremental=incremental)
            elif data == 'map_all_network':
                self._collected_data[data] = context().asset_server.get_network_profile(network_url=None, incremental=incremental)
            elif data == 'map_all_app':
                self._collected_data[data] = context().asset_server.get_application_details(incremental=incremental)
            elif data == 'map_sql_database':
                self._collected_data[data] = context().asset_server.get_all_sql_databases()
            elif data == 'map_all_container':
                self._collected_data[data] = context().asset_server.get_container_details(None, incremental)
            elif data == 'map_data_administrative':
                self._collected_data[data] = context().asset_server.get_administrative_logs(context().last_model_state_id)
            elif data == 'updates_deletes':
                self._collected_data[data] = self.update_delete_nodes(self._get_collected_data('map_data_administrative'))
        
        return self._collected_data[data]
    
    # asset node creation utility
    def create_asset_host(self, incremental=True):
        asset_list = []
        deletes = []
        # initial import case
        if not incremental:
            data = self._get_collected_data('map_all_vmachine', incremental)
            for record in data["value"]:
                key = dict()
                key["vm_map"] = record
                asset_list.append(key)
        # incremental import create/update case
        elif incremental:
            data = self._get_collected_data('updates_deletes', incremental)
            if data["vm"]["update"]:
                for resource_id in data["vm"]["update"]:
                    vm_data = context().asset_server.get_virtual_machine_details(resource_id, incremental)
                    if len(vm_data) > 1:
                        key = dict()
                        key["vm_map"] = vm_data
                        asset_list.append(key)
            # incremental import delete case
            if data["vm"]["delete"]:
                for resource_id in data["vm"]["delete"]:
                    search_result = context().car_service.graph_search('asset', context().args.source + ':' +
                                                                    convert_lower(resource_id))
                    if search_result['result']:
                        deletes.append(convert_lower(resource_id))
                if deletes:
                    self.delete_data['asset'].append(deletes)

        return asset_list


    # ipaddress node creation utility
    def create_ipaddress_macaddress(self, incremental=True):
        network_list = []
        update_network = []
        # initial import case
        if not incremental:
            data = self._get_collected_data('map_all_network', incremental)
            for record in data["value"]:
                for ipconfig in record["properties"]["ipConfigurations"]:
                    ipconfig_updated = self.network_intermediate_process(ipconfig)
                    if ipconfig_updated["properties"]["primary"]:
                        record["properties"]["ipConfigurations"] = ipconfig_updated
                        key = dict()
                        key["network_map"] = record
                        network_list.append(key)
        # incremental import create/update case
        elif incremental:
            data = self._get_collected_data('updates_deletes', incremental)
            if data["network"]["update"]:
                for resource_id in data["network"]["update"]:
                    network_data = context().asset_server.get_network_profile(resource_id, incremental)
                    if len(network_data) > 1:
                        for ipconfig in network_data["properties"]["ipConfigurations"]:
                            ipconfig_updated = self.network_intermediate_process(ipconfig)
                            if ipconfig_updated["properties"]["primary"]:
                                network_data["properties"]["ipConfigurations"] = ipconfig_updated
                                key = dict()
                                key["network_map"] = network_data
                                self.updates_ipaddress(key, update_network, network_list)

        return network_list, update_network

    # vulnerability node creation utility
    def create_vulnerability(self, incremental=True):
        vuln_list = []
        data = self._get_collected_data('map_data_security', incremental)
        if data["value"]:
            for record in data["value"]:
                # check to eliminate duplicate rows
                if context().args.switch:
                    if record["correlationId"] == record["eventDataId"]:
                        compromised_entity = deep_get(record, ["properties", "compromisedEntity"])
                        resource_type = deep_get(record, ["properties", "resourceType"])
                        r_group = record["resourceGroupName"]
                        # fetch external ID according to the resource and its type
                        if resource_type == "Virtual Machine":
                            record["vm_map"] = context().asset_server.get_virtual_machine_details_by_name(compromised_entity,
                                                                                                    r_group)
                        elif resource_type == "App Service":
                            record["application_map"] = context().asset_server.get_application_details_by_name(
                                compromised_entity,
                                r_group)
                        elif resource_type == "SQL Database":
                            server = deep_get(record, ["properties", "server"])
                            record["database_map"] = context().asset_server.get_sql_database_details_by_name(
                                compromised_entity, server, r_group)

                        vuln_list.append(record)
                elif not context().args.switch:
                    vuln_list.append(record)

        return vuln_list

    # application node creation utility
    def create_application(self, incremental=True):
        application_list = []
        update_ip = []
        # initial import case
        if not incremental:
            data = self._get_collected_data('map_all_app', incremental)
            for record in data["value"]:
                key = dict()
                key["application_map"] = record
                application_list.append(key)
        # incremental import create/update case
        elif incremental:
            deletes = []
            data = self._get_collected_data('updates_deletes', incremental)
            if data["application"]["update"] or data["app_host"]["update"]:
                for resource_id in data["application"]["update"] or data["app_host"]["update"]:
                    app_data = context().asset_server.get_application_details(resource_id, incremental)
                    if len(app_data) > 1:
                        key = dict()
                        key["application_map"] = app_data
                        self.updates_ipaddress(key, update_ip, application_list)
            # incremental import delete case
            if data["application"]["delete"]:
                for resource_id in data["application"]["delete"]:
                    search_result = context().car_service.graph_search('asset', context().args.source + ':' +
                                                                    convert_lower(resource_id))
                    if search_result['result']:
                        deletes.append(convert_lower(resource_id))
                if deletes:
                    self.delete_data['asset'].append(deletes)
                    self.delete_data['application'].append(deletes)

        return application_list, update_ip


    # database node creation utility
    def create_database(self, incremental=True):
        database_list = []
        initial_db_list = []
        server_list = []
        deletes_db = []
        deletes_server = []
        # initial import case
        if not incremental:
            data = self._get_collected_data('map_sql_database', incremental)
            for record in data["value"]:
                key = dict()
                key["database_map"] = record
                initial_db_list.append(key)
        # incremental import create/update case
        elif incremental:
            data = self._get_collected_data('updates_deletes', incremental)
            if data["database"]["update"]:
                for resource_id in data["database"]["update"]:
                    db_data = context().asset_server.get_sql_database_details(resource_id)
                    if len(db_data) > 1:
                        key = dict()
                        key["database_map"] = db_data
                        self.updates_database(key, server_list, database_list)
            # incremental import delete case
            if data["database"]["delete"]:
                for resource_id in data["database"]["delete"]:
                    search_result = context().car_service.graph_search('database', context().args.source + ':' +
                                                                    convert_lower(resource_id))
                    if search_result['result']:
                        deletes_db.append(convert_lower(resource_id))
                if deletes_db:
                    self.delete_data['database'].append(deletes_db)
            if data["server"]["delete"]:
                for resource_id in data["server"]["delete"]:
                    search_result = context().car_service.graph_search('asset', context().args.source + ':' +
                                                                    convert_lower(resource_id))
                    if search_result['result']:
                        deletes_server.append(convert_lower(resource_id))
                if deletes_server:
                    self.delete_data['asset'].append(deletes_server)

        return initial_db_list, server_list, database_list

    # container node creation utility (NEEDS CONFIRMATION)
    # def create_container(self, incremental=True):
    #     container_list = []
    #     deletes = []
    #     if not incremental:
    #         data = self._get_collected_data('map_all_container', incremental)
    #         for record in data["value"]:
    #             key = dict()
    #             key["container_map"] = record
    #             container_list.append(key)
    #     elif incremental:
    #         data = self._get_updates_deletes()
    #         if data["container"]["update"]:
    #             for resource_id in data["container"]["update"]:
    #                 con_data = context().asset_server.get_container_details(resource_id, incremental)
    #                 if len(con_data) > 1:
    #                     key = dict()
    #                     key["container_map"] = con_data
    #                     container_list.append(key)
    #         if data["container"]["delete"]:
    #             for resource_id in data["container"]["delete"]:
    #                 search_result = context().car_service.graph_search('asset', convert_lower(resource_id))
    #                 if search_result['result']:
    #                     deletes.append(convert_lower(resource_id))
    #             if deletes:
    #                 self.delete_data['asset'].append(deletes)
    #
    #     GraphProcessor(self, container_list, consume.asset_consumer, consume.container_consumer,
    #                    consume.report_container_consumer,
    #                    consume.asset_container_consumer, consume.asset_hostname_consumer).process()
    #     return consume.asset_consumer.result, consume.container_consumer.result, consume.report_container_consumer.result, \
    #            consume.asset_container_consumer.result, consume.asset_hostname_consumer.result


    def network_intermediate_process(self, ipconfig):
        # condition to fetch the primary ip-configuration
        if ipconfig["properties"]["primary"]:
            public_ip_url = ipconfig.get('properties', {}).get('publicIPAddress', {}).get('id')
            temp = dict()
            if public_ip_url is not None:
                response_data = context().asset_server.get_public_ipaddress(public_ip_url)
                public_ip = response_data.get('properties', {}).get('ipAddress')
                host = response_data.get('properties', {}).get('dnsSettings', {}).get('fqdn', {})
                if public_ip is not None:
                    temp["public"] = public_ip
                    temp["private"] = ipconfig["properties"]["privateIPAddress"]
                    ipconfig["properties"]["IPAddress"] = temp
                else:
                    temp["private"] = ipconfig["properties"]["privateIPAddress"]
                    ipconfig["properties"]["IPAddress"] = temp

                if host is not None:
                    ipconfig["properties"]["fqdn"] = host
            else:
                temp["private"] = ipconfig["properties"]["privateIPAddress"]
                ipconfig["properties"]["IPAddress"] = temp

        return ipconfig


    # asset node creation utility
    def update_hostname_app(self, incremental=True):
        host_list = []
        # incremental import create/update case
        if incremental:
            data = self._get_collected_data('updates_deletes', incremental)
            if data["app_host"]["update"]:
                for resource_id in data["app_host"]["update"]:
                    app_data = context().asset_server.get_application_details(resource_id, incremental)
                    if len(app_data) > 1:
                        key = dict()
                        key["application_map"] = app_data
                        self.updates_hostname(key, host_list, [])
        return host_list


    # asset node creation utility
    def update_hostname_vm(self, incremental=True):
        host_list = []
        # incremental import create/update case
        if incremental:
            data = self._get_collected_data('updates_deletes', incremental)
            if data["public_ip"]["update"]:
                for resource_id in data["public_ip"]["update"]:
                    response_data = context().asset_server.get_public_ipaddress(resource_id)
                    if len(response_data) > 1 and deep_get(response_data, ['properties', 'ipConfiguration', 'id']):
                        host = response_data.get('properties', {}).get('dnsSettings', {}).get('fqdn', {})
                        network_url = deep_get(response_data, ['properties', 'ipConfiguration', 'id']).split('/')
                        network_response = context().asset_server.get_network_profile("/".join(network_url[:9]), incremental)
                        vm = network_response.get('properties', {}).get('virtualMachine', {}).get('id', {})
                        if vm and host:
                            key = dict()
                            key["network_map"] = response_data
                            key = {"network_map": {"properties": {"ipConfigurations": {"properties": {"fqdn": host}},
                                                                "virtualMachine": {"id": vm}}}}
                            self.updates_hostname(key, host_list, [])
        return host_list

    # segregation of activity log external IDs based on create/update or delete case
    def update_delete_nodes(self, data):
        """Get the logs from azure management administrative logs endpoint
            and filter the logs based on operation types.
        :param context: global context object
        :param data: dict, response from administrative logs endpoint
        :return: dict, based on resource and operation type
        """
        update_data = dict()
        # dict initialization for multiple resources
        update_list = ["vm", "application", "database", "container", "network", "public_ip", "server", "app_host"]
        type_list = ["update", "delete"]
        for values in update_list:
            update_data[values] = {}
            for types in type_list:
                update_data[values][types] = []

        for record in data["value"]:
            # vm create/update
            if record["operationName"]["value"] == 'Microsoft.Compute/virtualMachines/write' \
                    and record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "":
                if record['resourceId'] not in update_data["vm"]["update"] and \
                        record['resourceId'] not in update_data["vm"]["delete"]:
                    update_data["vm"]["update"].append(record['resourceId'])
            # vm delete
            elif record["operationName"]["value"] == 'Microsoft.Compute/virtualMachines/delete' \
                    and record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "":
                if record['resourceId'] not in update_data["vm"]["update"] and \
                        record['resourceId'] not in update_data["vm"]["delete"]:
                    update_data["vm"]["delete"].append(record['resourceId'])
                    # to discard updates of a deleted VM resource
                elif record['resourceId'] in update_data["vm"]["update"]:
                    update_data["vm"]["update"].remove(record['resourceId'])
                    update_data["vm"]["delete"].append(record['resourceId'])
            # application create/update
            elif record["status"]["value"] == "Succeeded" \
                    and record["operationName"]["value"] == "Microsoft.Web/sites/write":
                if record['resourceId'] not in update_data["application"]["update"] and \
                        record['resourceId'] not in update_data["application"]["delete"]:
                    update_data["application"]["update"].append(record['resourceId'])
            # application delete
            elif record["operationName"]["value"] == 'Microsoft.Web/sites/delete' \
                    and record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "":
                if record['resourceId'] not in update_data["application"]["update"] and \
                        record['resourceId'] not in update_data["application"]["delete"]:
                    update_data["application"]["delete"].append(record['resourceId'])
                    # to discard updates of a deleted application resource
                elif record['resourceId'] in update_data["application"]["update"]:
                    update_data["application"]["update"].remove(record['resourceId'])
                    update_data["application"]["delete"].append(record['resourceId'])
            # database create/update
            elif record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "" and \
                    record["operationName"]["value"] == "Microsoft.Sql/servers/databases/write":
                if record['resourceId'] not in update_data["database"]["update"] and \
                        record['resourceId'] not in update_data["database"]["delete"]:
                    update_data["database"]["update"].append(record['resourceId'])
            # database delete
            elif record["operationName"]["value"] == 'Microsoft.Sql/servers/databases/delete' \
                    and record["status"]["value"] == "Succeeded" \
                    and record["subStatus"]["value"] == "":
                if record['resourceId'] not in update_data["database"]["update"] and \
                        record['resourceId'] not in update_data["database"]["delete"]:
                    update_data["database"]["delete"].append(record['resourceId'])
                    # to discard updates of a deleted database resource
                elif record['resourceId'] in update_data["database"]["update"]:
                    update_data["database"]["update"].remove(record['resourceId'])
                    update_data["database"]["delete"].append(record['resourceId'])
            # network create/update
            elif record["operationName"]["value"] == "Microsoft.Network/networkInterfaces/write" \
                    and record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "":
                if record['resourceId'] not in update_data["network"]["update"] and \
                        record['resourceId'] not in update_data["network"]["delete"]:
                    update_data["network"]["update"].append(record['resourceId'])
            # network delete
            elif record["operationName"]["value"] == "Microsoft.Network/networkInterfaces/delete" \
                    and record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "":
                if record['resourceId'] not in update_data["network"]["update"] and \
                        record['resourceId'] not in update_data["network"]["delete"]:
                    update_data["network"]["delete"].append(record['resourceId'])
                    # to discard updates of a deleted network resource
                elif record['resourceId'] in update_data["network"]["update"]:
                    update_data["network"]["update"].remove(record['resourceId'])
                    update_data["network"]["delete"].append(record['resourceId'])
            # container create/update
            elif record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "" \
                    and record["operationName"]["value"] == "Microsoft.ContainerInstance/containerGroups/write":
                if record['resourceId'] not in update_data["container"]["update"]:
                    update_data["container"]["update"].append(record['resourceId'])
            # container delete
            elif record["operationName"]["value"] == 'Microsoft.ContainerInstance/containerGroups/delete' \
                    and record["status"]["value"] == "Succeeded" \
                    and record["subStatus"]["value"] == "":
                if record['resourceId'] not in update_data["container"]["delete"]:
                    update_data["container"]["delete"].append(record['resourceId'])
            # public ip addresses create/update
            elif record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "" \
                    and record["operationName"]["value"] == "Microsoft.Network/publicIPAddresses/write":
                if record['resourceId'] not in update_data["public_ip"]["update"]:
                    update_data["public_ip"]["update"].append(record['resourceId'])
            # app service hostname create/update (custom domains)
            elif record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "OK" \
                    and record["operationName"]["value"] == "Microsoft.Web/sites/publishxml/action":
                if record['resourceId'] not in update_data["app_host"]["update"]:
                    update_data["app_host"]["update"].append(record['resourceId'])
            # SQL server delete
            elif record["operationName"]["value"] == 'Microsoft.Sql/servers/delete' \
                    and record["status"]["value"] == "Succeeded" \
                    and record["subStatus"]["value"] == "":
                if record['resourceId'] not in update_data["server"]["delete"]:
                    update_data["server"]["delete"].append(record['resourceId'])
            # public ip addresses update for VM re-start
            elif record["status"]["value"] == "Succeeded" and record["subStatus"]["value"] == "" \
                    and record["operationName"]["value"] == "Microsoft.Compute/virtualMachines/start/action":
                resource_id = record["resourceId"]
                network_interface = context().asset_server.get_virtual_machine_details(resource_id)
                interfaces = deep_get(network_interface, ["properties", "networkProfile", "networkInterfaces"])[0]
                if interfaces["id"] not in update_data["network"]["update"] and \
                        interfaces["id"] not in update_data["network"]["delete"]:
                    update_data["network"]["update"].append(interfaces["id"])
        return update_data


    def updates_ipaddress(self, data, update_network, network_list):
        """Logic to check update of IPAddress for VMs and app services in the incremental import run.
        :param context: object, global context instance
        :param data: dict, response from administrative logs endpoint
        :param update_network: list, list to append only updated resource data
        :param network_list: list, list to append all created resource data
        """
        destination_ip, temp, asset_id = set(), {}, None

        if "network_map" in data:
            asset_id = deep_get(data, ["network_map", "properties", "virtualMachine", "id"])
            private_ip = deep_get(data,
                                ["network_map", "properties", "ipConfigurations", "properties", "IPAddress", "private"])
            public_ip = deep_get(data,
                                ["network_map", "properties", "ipConfigurations", "properties", "IPAddress", "public"])

            if asset_id:
                # verification of IP value against CAR DB existing entries to identify the create/update case in VM
                search_result = context().car_service.graph_search('asset', convert_lower(asset_id))

                if search_result['result'] and search_result['related']:
                    for car_ip in search_result['related']:
                        if 'ipaddress/' in str(deep_get(car_ip, ["node", "_id"])) and deep_get(car_ip, ["node", "_key"]) \
                                and context().args.source in deep_get(car_ip, ["link", "source"]):
                            destination_ip.add(deep_get(car_ip, ["node", "_key"]))
                    if public_ip:
                        # multiple scenarios of IP update in a VM
                        if private_ip not in destination_ip and public_ip not in destination_ip:
                            update_network.append(data)
                            context().logger.debug("Updating both Public IP and Private IP")
                        elif private_ip in destination_ip and public_ip not in destination_ip:
                            temp['public'] = public_ip
                            data["network_map"]["properties"]["ipConfigurations"]["properties"]["IPAddress"] = temp
                            update_network.append(data)
                            context().logger.debug("Updating Public IP only")
                            destination_ip.discard(private_ip)
                        elif private_ip not in destination_ip and public_ip in destination_ip:
                            temp['private'] = private_ip
                            data["network_map"]["properties"]["ipConfigurations"]["properties"]["IPAddress"] = temp
                            update_network.append(data)
                            context().logger.debug("Updating Private IP only")
                            destination_ip.discard(public_ip)
                        else:
                            destination_ip.discard(public_ip)
                            destination_ip.discard(private_ip)
                    else:
                        if private_ip not in destination_ip:
                            temp['private'] = private_ip
                            data["network_map"]["properties"]["ipConfigurations"]["properties"]["IPAddress"] = temp
                            update_network.append(data)
                            context().logger.debug("Updating Private IP")
                        elif private_ip in destination_ip:
                            destination_ip.discard(private_ip)
                elif search_result['result'] is None and search_result['related'] == []:
                    network_list.append(data)
                    context().logger.debug("VM Creation Scenario for new IPs")

        elif "application_map" in data:
            asset_id = deep_get(data, ["application_map", "id"])
            inbound_ip = deep_get(data, ["application_map", "properties", "inboundIpAddress"])
            if asset_id and inbound_ip:
                # verification of IP value against existing entries of CAR DB to identify the create/update case in apps
                search_result = context().car_service.graph_search('asset', context().args.source + ':' + convert_lower(asset_id))

                if search_result['result'] and search_result['related']:
                    for value in search_result['related']:
                        if 'ipaddress/' in str(deep_get(value, ["node", "_id"])) and deep_get(value, ["node", "_key"]) \
                                and context().args.source in deep_get(value, ["link", "source"]):
                            destination_ip.add(deep_get(value, ["node", "_key"]))
                    if inbound_ip not in destination_ip:
                        update_network.append(data)
                        context().logger.debug("Updating inbound IP for existing app resource")
                    elif inbound_ip in destination_ip:
                        destination_ip.discard(inbound_ip)

                elif search_result['result'] is None and search_result['related'] == []:
                    network_list.append(data)
                    context().logger.debug("App Creation Scenario for new IPs")

        for ip in destination_ip:  # edge turn off for ip
            temp = dict()
            temp['from'] = convert_lower(asset_id)
            temp['to'] = ip
            temp['edge_type'] = 'asset_ipaddress'
            self.update_edge.append(temp)


    def updates_hostname(self, data, update_list, host_list):
        """Logic to check update of Hostname for VMs, app services, and SQL-databases in the incremental import run.
        :param context: object, global context instance
        :param data: dict, response from administrative logs endpoint
        :param update_list: list, list to append only updated resource data
        :param host_list: list, list to append all created resource data
        """
        asset_id = None
        host = []
        update_host = set()

        if "network_map" in data:
            host.append(deep_get(data, ["network_map", "properties", "ipConfigurations", "properties", "fqdn"]))
            asset_id = deep_get(data, ["network_map", "properties", "virtualMachine", "id"])
        elif "application_map" in data:
            host.extend(deep_get(data, ["application_map", "properties", "hostNames"]))
            asset_id = deep_get(data, ["application_map", "id"])

        if asset_id and host:
            # verification of host value against CAR DB existing entries to identify the create/update case
            search_result = context().car_service.graph_search('asset', context().args.source + ':' + convert_lower(asset_id))

            if search_result['result'] and search_result['related']:
                for value in search_result['related']:
                    if 'hostname/' in str(deep_get(value, ["node", "_id"])) and deep_get(value, ["node", "_key"])\
                            and context().args.source in deep_get(value, ["link", "source"]):
                        update_host.add(deep_get(value, ["node", "_key"]))
                for domain in host:
                    if domain not in update_host:
                        if "application_map" in data:
                            data["application_map"]["properties"]["hostNames"] = [domain]
                        update_list.append(data)
                        context().logger.debug("Updating hostname for existing resource")
                    elif domain in update_host:
                        update_host.discard(domain)

                for old_host in update_host:    # edge turn off for host
                    temp = dict()
                    temp['from'] = convert_lower(asset_id)
                    temp['to'] = old_host
                    temp['edge_type'] = 'asset_hostname'
                    self.update_edge.append(temp)

            elif search_result['result'] is None and search_result['related'] == []:
                host_list.append(data)
                context().logger.debug("Creating hostname for new resource")


    def updates_database(self, data, server_list, db_list):
        """Logic to check generic update of SQL-databases in the incremental import run.
        :param context: object, global context instance
        :param data: dict, response from administrative logs endpoint
        :param server_list: list, list to append all created resource data
        :param db_list: list, list to append all created resource data
        """
        asset_id, database_id = None, None

        if "database_map" in data:
            asset_id = deep_get(data, ["database_map", "server_map", "id"])
            database_id = deep_get(data, ["database_map", "id"])

        if asset_id:
            # verification against CAR DB existing entries to identify the create/update case - sql server
            search_result = context().car_service.graph_search('asset', context().args.source + ':' + convert_lower(asset_id))

            if search_result['result'] is None and search_result['related'] == []:
                server_list.append(data)
                context().logger.debug("Creating scenario for new server resource")

        if database_id:
            # verification against CAR DB existing entries to identify the create/update case - sql database
            search_result = context().car_service.graph_search('database', convert_lower(database_id))

            if search_result['result'] is None and search_result['related'] == []:
                db_list.append(data)
                context().logger.debug("Creating scenario for new database resource")


    def vulnerability_patch(self):
        """edge turn off for vulnerability"""
        alert_list = list()
        data = self._get_collected_data('map_data_administrative')
        for record in data["value"]:
            asset_list = list()
            # vulnerability update
            if record["operationName"]["value"] == 'Microsoft.Security/locations/alerts/Dismiss/action' and \
                    record["resourceId"]:
                alert_id = record["resourceId"].split('/')[-1]
                if alert_id not in alert_list:
                    alert_list.append(alert_id)
                    search_result = context().car_service.graph_search('vulnerability', context().args.source + ':' + alert_id)
                    for value in search_result['related']:
                        if 'asset/' in str(deep_get(value, ["node", "_id"])) and deep_get(value, ["node", "external_id"]) \
                                and context().args.source in deep_get(value, ["node", "source"]):
                            asset_list.append(deep_get(value, ["node", "external_id"]))
                    for asset_id in asset_list:
                        temp = dict()
                        temp['from'] = asset_id
                        temp['to'] = alert_id
                        temp['edge_type'] = 'asset_vulnerability'
                        self.update_edge.append(temp)


    def update_edges(self):
        context().logger.info('Disabling edges')
        for edge in self.update_edge:
            if 'last_modified' in edge:
                context().car_service.edge_patch(context().args.source, edge, {"last_modified": edge['last_modified']})
            else:
                context().car_service.edge_patch(context().args.source, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.update_edge))


    def delete_vertices(self):
        """Summary: Delete the vertices."""
        context().logger.info('Deleting vertices')
        for vertex in self.delete_data:
            context().car_service.delete(vertex, self.delete_data[vertex])
        
        context().logger.info('Deleting vertices done: %s', {
            'asset': len(self.delete_data['asset']),
            'application': len(self.delete_data['application']),
            'database': len(self.delete_data['database'])
        })

