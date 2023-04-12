import json
from datetime import datetime, timedelta

from car_framework.context import context

# This is to disable context().fooMember error in IDE
# pylint: disable=no-member

QUERY_FORMAT = r"('{}')"

def deep_get(_dict, keys, default=None):
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict


def get_n_days_ago(days_ago=15):
    date_n_days_ago = datetime.now() - timedelta(days=days_ago)
    return date_n_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def timestamp_conv(time_string):
    time_pattern = "%Y-%m-%dT%H:%M:%S"
    epoch = datetime(1970, 1, 1)
    converted_time = int(((datetime.strptime(str(time_string)[:19], time_pattern) - epoch).total_seconds()) * 1000)
    return converted_time


def epoch_to_datetime_conv(epoch_time):
        epoch_time = float(epoch_time) / 1000.0
        datetime_time = datetime.fromtimestamp(epoch_time)
        return datetime_time


def datetime_format_to_ISO_8601(dt):
        time_pattern = "%Y-%m-%dT%H:%M:%SZ"
        return dt.strftime(time_pattern)


def parse_machine_ids(map_all_machine, flag=True):
    """Combining machine ids for query"""
    temp, list_id, n = [], [], 150
    for record in map_all_machine:
        if flag:
            if record['healthStatus'] in \
                    ['Active', 'ImpairedCommunication', 'NoSensorData', 'NoSensorDataImpairedCommunication']:
                temp.append(record['id'])
        elif not flag:
            temp.append(record['id'])
    final = [temp[i * n:(i + 1) * n] for i in range((len(temp) + n - 1) // n)]
    for ids in final:
        if len(ids) != 1:
            list_id.append(tuple(ids))
        elif len(ids) == 1:
            list_id.append(QUERY_FORMAT.format(ids[0]))
    return list_id


def convert_mac_format(string):
    groups = [string[i:i + 2] for i in range(0, len(string), 2)]
    return ':'.join(groups)


def create_logic_check(compare_time):
    if len(compare_time) == 28:
        first_seen_time = datetime.strptime(compare_time[:-2] + 'Z', "%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        first_seen_time = datetime.strptime(compare_time, "%Y-%m-%dT%H:%M:%S.%fZ")

    last_runtime = datetime.strptime(datetime_format_to_ISO_8601(epoch_to_datetime_conv(context().last_model_state_id)), "%Y-%m-%dT%H:%M:%SZ")
    # create flag
    if first_seen_time >= last_runtime:
        return True
    else:
        # update flag
        return False


class DataCollector(object):

    _collected_data = {}
    user_list, update_edge = list(), list()

    def _get_collected_data(self, data):
        if not self._collected_data.get(data):
            if data == 'all_machine':
                self._collected_data[data] = context().asset_server.get_machine_list()
            elif data == 'incremental_machine':
                self._collected_data[data] = context().asset_server.get_machine_list(
                    timestamp=datetime_format_to_ISO_8601(epoch_to_datetime_conv(context().last_model_state_id)),
                    curr_time=datetime_format_to_ISO_8601(epoch_to_datetime_conv(context().new_model_state_id)))
        
        return self._collected_data[data]
    
    def create_asset_host(self, incremental=True):
        """asset node creation for initial and incremental report"""
        asset_list = []
        
        # initial import case
        if not incremental:
            data = self._get_collected_data('all_machine')
            asset_list.extend(data["value"])

        elif incremental:
            data = self._get_collected_data('incremental_machine')
            for record in data["value"]:
                # create
                create_logic = create_logic_check(record['firstSeen'])
                if create_logic:
                    asset_list.append(record)
        return asset_list


    def create_ipaddress_macaddress(self, incremental=True):
        """ip_address mac_address node creation for initial and incremental report"""
        network_lookup, network_list = list(), list()
        ip_data, mac_data, ip_mac = list(), list(), list()

        if incremental:
            data = self._get_collected_data('incremental_machine')
        else:
            data = self._get_collected_data('all_machine')

        list_ids = parse_machine_ids(data['value'], False)

        for asset_ids in list_ids:
            if incremental: 
                ip_lookup = context().asset_server.mac_private_ip_information(incremental, asset_ids, 
                                datetime_format_to_ISO_8601(epoch_to_datetime_conv(context().last_model_state_id)),
                                datetime_format_to_ISO_8601(epoch_to_datetime_conv(context().new_model_state_id)))
            else:
                ip_lookup = context().asset_server.mac_private_ip_information(incremental, asset_ids)

            if ip_lookup['Results']:
                network_lookup.extend(ip_lookup['Results'])

        if not incremental:  # initial import case
            self.create_mac_ipv6(data, network_lookup, network_list)
        
        elif incremental:  # incremental import case
            raw_data, new_asset = list(), list()
            self.create_mac_ipv6(data, network_lookup, raw_data)
            for record in raw_data:
                create_logic = create_logic_check(record['firstSeen'])
                if create_logic:  # create
                    network_list.append(record)
                else:  # update
                    new_asset.append(record)

            asset_inc_list = self.updates_network_address(new_asset, ip_data, mac_data, ip_mac)
            if asset_inc_list:  # delete edge case
                network_list.extend(asset_inc_list)
            for user_update in network_list:
                user_response = context().asset_server.get_user_information(user_update['id'])
                if user_response["value"]:
                    for users in user_response["value"]:
                        users['DeviceId'] = user_update['id']
                        users['DeviceName'] = user_update['computerDnsName']
                        self.user_list.append(users)

        return network_list, ip_data, mac_data, ip_mac


    def create_mac_ipv6(self, data, network_lookup, network, incremental=True):
        """Private Api call for initial and incremental report"""
        for machine in data["value"]:
            machine['MacAddress'] = None
            private_ip, ipaddress_collection = set(), set()
            for network_data in network_lookup:
                count = 0
                for ips in json.loads(network_data['IPAddresses']):
                    if ips['IPAddress'] == machine['lastIpAddress']:
                        if machine['id'] == network_data['DeviceId']:
                            count = count + 1
                            machine['MacAddress'] = convert_mac_format(network_data['MacAddress'])
                            private_ip.add(ips['IPAddress'])
                            ipaddress_collection.add(ips['IPAddress'])
                    if count == 1 and ips['SubnetPrefix'] == 64 and ips['AddressType'] == 'Private':
                        private_ip.add(ips['IPAddress'])
                        ipaddress_collection.add(ips['IPAddress'])
                if count == 1:
                    break
            ipaddress_collection.add(machine['lastExternalIpAddress'])
            if private_ip != set() and ipaddress_collection != set() and machine['MacAddress']:
                machine['lastIpAddress'] = list(private_ip)
                machine['IPAddress'] = list(ipaddress_collection)
                network.append(machine)
            elif machine['lastExternalIpAddress'] and machine['MacAddress'] is None and machine['lastIpAddress'] is None:
                machine['IPAddress'] = [machine['lastExternalIpAddress']]
                machine['lastIpAddress'] = list()
                network.append(machine)


    def create_vulnerability(self, incremental=True):
        """vulnerability node creation for initial and incremental report"""
        vuln_list = []
        vuln_update = dict()
        
        application_create = None
        vulnerability_update = None
        app_vuln_edge = None
        vulnerability_create = None

        if not incremental:  # initial import case
            data = self._get_collected_data('all_machine')
            if context().args.vuln is None:
                vuln_ids = parse_machine_ids(data['value'], False)
                for asset_id in vuln_ids:
                    vuln_response = context().asset_server.vulnerability_information(asset_id)
                    if vuln_response['Results']:
                        vuln_list.extend(vuln_response['Results'])
            if context().args.alerts is None:
                map_alerts = context().asset_server.get_alerts_list()
                if map_alerts["value"]:
                    vuln_list.extend(map_alerts["value"])

        if incremental:
            data = self._get_collected_data('incremental_machine')
            if context().args.alerts is None:  # incremental import case for alerts
                self.alerts_update(vuln_list)
            if context().args.vuln is None:  # incremental import case for vulnerability
                self.vulnerability_update(data, vuln_update)
                application_create = vuln_update.get('application_create', [])
                vulnerability_update = vuln_update.get('vulnerability_update', [])
                app_vuln_edge = vuln_update.get('app_vuln_edge', [])
                vulnerability_create = vuln_update.get('vulnerability_create', [])

        return vuln_list, application_create, vulnerability_update, app_vuln_edge, vulnerability_create


    def create_user(self, incremental=True):
        """user node creation for initial and incremental report"""
        if not incremental:  # initial import case
            data = self._get_collected_data('all_machine')
            for machine_info in data['value']:
                user_response = context().asset_server.get_user_information(machine_info['id'])
                if user_response["value"]:
                    for users in user_response["value"]:
                        users['DeviceId'] = machine_info['id']
                        users['DeviceName'] = machine_info['computerDnsName']
                        self.user_list.append(users)

        return self.user_list



    def updates_network_address(self, new_asset, ip_data, mac_data, ip_mac):
        """Summary: updating IpAddress, MacAddress and users of Asset."""
        inc_asset = list()
        for machine_id in new_asset:
            destination_users, destination_ips, destination_macs = set(), set(), set()
            search_result = context().car_service.graph_search('asset', context().args.CONNECTION_NAME + ':' + machine_id['id'])
            if search_result['result'] and search_result['related']:
                for car_ip in search_result['related']:
                    if 'ipaddress/' in str(deep_get(car_ip, ["node", "_id"])) and deep_get(car_ip, ["node", "_key"]) \
                            and context().args.CONNECTION_NAME in deep_get(car_ip, ["link", "source"]):
                        destination_ips.add(deep_get(car_ip, ["node", "_key"]))
                    if 'macaddress/' in str(deep_get(car_ip, ["node", "_id"])) and deep_get(car_ip, ["node", "_key"]) \
                            and context().args.CONNECTION_NAME in deep_get(car_ip, ["link", "source"]):
                        destination_macs.add(deep_get(car_ip, ["node", "_key"]))
                    if 'account/' in str(deep_get(car_ip, ["node", "_id"])) and deep_get(car_ip, ["node", "external_id"]) and \
                            context().args.CONNECTION_NAME in deep_get(car_ip, ["node", "source"]):
                        destination_users.add(deep_get(car_ip, ["node", "external_id"]))

                # Public ip (ip vertice/asset ip)
                if machine_id['lastExternalIpAddress'] not in destination_ips:
                    public_ip = dict()
                    public_ip['id'] = machine_id['id']
                    public_ip['IPAddress'] = [machine_id['lastExternalIpAddress']]
                    ip_data.append(public_ip)
                elif machine_id['lastExternalIpAddress'] in destination_ips:
                    destination_ips.discard(machine_id['lastExternalIpAddress'])

                # Mac address (mac vertices, asset mac)
                if machine_id['MacAddress'] and machine_id['MacAddress'] not in destination_macs:
                    mac_address = dict()
                    mac_address['id'] = machine_id['id']
                    mac_address['MacAddress'] = machine_id['MacAddress']
                    mac_data.append(mac_address)
                elif machine_id['MacAddress'] and machine_id['MacAddress'] in destination_macs:
                    destination_macs.discard(machine_id['MacAddress'])

                # Private ip (ip mac)
                if machine_id['lastIpAddress']:
                    for inc_ip in machine_id['lastIpAddress']:
                        if inc_ip not in destination_ips:
                            temp, asset_ip = dict(), dict()
                            temp['id'] = machine_id['id']
                            temp['lastIpAddress'] = [inc_ip]
                            temp['MacAddress'] = machine_id['MacAddress']
                            asset_ip['id'] = machine_id['id']
                            asset_ip['IPAddress'] = [inc_ip]
                            ip_data.append(asset_ip)
                            ip_mac.append(temp)
                        elif inc_ip in destination_ips:
                            destination_ips.discard(inc_ip)
                            search_ip = context().car_service.graph_search('ipaddress', inc_ip)
                            update_mac = set()
                            if search_ip['related']:
                                for car_ip in search_ip['related']:
                                    if 'macaddress/' in str(deep_get(car_ip, ["node", "_id"])) and \
                                            deep_get(car_ip, ["node", "key"]) and context().args.CONNECTION_NAME in \
                                            deep_get(car_ip, ["node", "source"]):
                                        update_mac.add(deep_get(car_ip, ["node", "key"]))
                            if machine_id['MacAddress'] not in update_mac:
                                temp = dict()
                                temp['id'] = machine_id['id']
                                temp['lastIpAddress'] = machine_id['lastIpAddress']
                                temp['MacAddress'] = machine_id['MacAddress']
                                ip_mac.append(temp)
                # Users
                user_response = context().asset_server.get_user_information(machine_id['id'])
                if user_response['value']:
                    for users in user_response['value']:
                        if users['accountName'] not in destination_users:
                            users['DeviceId'] = machine_id['id']
                            users['DeviceName'] = machine_id['computerDnsName']
                            self.user_list.append(users)
                        elif users['accountName'] in destination_users:
                            destination_users.discard(users['accountName'])
                # edge update logic
                self.asset_ip_edge_update(machine_id['id'], destination_ips)
                self.asset_mac_edge_update(machine_id['id'], destination_macs)
                self.asset_account_update(machine_id['id'], destination_users)

            elif not search_result['related']:
                inc_asset.append(machine_id)

        return inc_asset


    def asset_ip_edge_update(self, machine_id, ip_list):
        """Summary: edge disable for asset ipaddress"""
        for old_id in ip_list:
            temp = dict()
            temp['from'] = machine_id
            temp['to'] = old_id
            temp['edge_type'] = 'asset_ipaddress'
            self.update_edge.append(temp)


    def asset_mac_edge_update(self, machine_id, mac_list):
        """Summary: edge disable for asset macaddress"""
        for old_mac in mac_list:
            temp = dict()
            temp['from'] = machine_id
            temp['to'] = old_mac
            temp['edge_type'] = 'asset_macaddress'
            self.update_edge.append(temp)


    def asset_account_update(self, machine_id, user_data):
        """Summary: edge disable for asset account"""
        for account in user_data:
            temp = dict()
            temp['from'] = machine_id
            temp['to'] = account
            temp['edge_type'] = 'asset_account'
            self.update_edge.append(temp)


    def alerts_update(self, vuln_list):
        """Summary: alerts for incremental update"""
        map_alerts = context().asset_server.get_alerts_list(True)
        if map_alerts['value']:
            for record in map_alerts['value']:
                create_alert = create_logic_check(record['alertCreationTime'])
                update_alert = create_logic_check(record['lastEventTime'])
                if record['status'] in ['New', 'InProgress']:
                    if create_alert:
                        vuln_list.append(record)
                    elif update_alert:
                        temp = dict()
                        temp['from'] = record['machineId']
                        temp['to'] = record['id']
                        temp['edge_type'] = 'asset_vulnerability'
                        temp['last_modified'] = timestamp_conv(record['lastEventTime'])
                        self.update_edge.append(temp)
                elif record['status'] == 'Resolved':
                    if create_alert:
                        vuln_list.append(record)
                        resolved_alert = create_logic_check(record['resolvedTime'])
                        if resolved_alert:
                            temp = dict()
                            temp['from'] = record['machineId']
                            temp['to'] = record['id']
                            temp['edge_type'] = 'asset_vulnerability'
                            self.update_edge.append(temp)
                    else:
                        resolved_alert = create_logic_check(record['resolvedTime'])
                        if resolved_alert:
                            temp = dict()
                            temp['from'] = record['machineId']
                            temp['to'] = record['id']
                            temp['edge_type'] = 'asset_vulnerability'
                            self.update_edge.append(temp)


    def vulnerability_update(self, data, update_data):
        """Summary: vulnerability for incremental update"""
        fields = ['vulnerability_create', 'application_create', 'vulnerability_update', 'app_vuln_edge']
        for values in fields:
            update_data[values] = list()
        vuln_collections, vuln_mapping = list(), dict()
        vuln_ids = parse_machine_ids(data['value'])
        for asset_id in vuln_ids:
            vuln_response = context().asset_server.vulnerability_information(asset_id)
            if vuln_response['Results']:
                vuln_collections.extend(vuln_response['Results'])
        for value in vuln_collections:
            if value['DeviceId'] not in vuln_mapping:
                vuln_mapping[value['DeviceId']] = list()
            vuln_mapping[value['DeviceId']].append(value)

        for machine_id in vuln_mapping:  # iterating asset for app vulnerability create and update
            search_result = context().car_service.graph_search('asset', context().args.CONNECTION_NAME + ':' + machine_id)
            dest_vuln, dest_app, temp_vuln, temp_app = list(), list(), set(), set()
            for car_data in search_result['related']:
                if 'vulnerability/' in str(deep_get(car_data, ["node", "_id"])) and \
                        deep_get(car_data, ["node", "disclosed_on"]) is None and context().args.CONNECTION_NAME in \
                        deep_get(car_data, ["node", "source"]):
                    dest_vuln.append(deep_get(car_data, ["node", "external_id"]))
                if 'application/' in str(deep_get(car_data, ["node", "_id"])) and context().args.CONNECTION_NAME in \
                        deep_get(car_data, ["node", "source"]):
                    dest_app.append(deep_get(car_data, ["node", "external_id"]))
            for value in vuln_mapping[machine_id]:
                vuln_id = value['CveId']
                app_id = value['SoftwareVendor'] + ':' + value['SoftwareName'] + ':' + value[
                    'SoftwareVersion']
                if app_id not in dest_app:  # Application create and update
                    if vuln_id not in dest_vuln:
                        update_data['vulnerability_create'].append(value)

                    elif vuln_id in dest_vuln:
                        temp_vuln.add(vuln_id)
                        update_data['application_create'].append(value)

                elif app_id in dest_app and vuln_id not in dest_vuln:  # vulnerability create
                    update_data['vulnerability_update'].append(value)
                    temp_app.add(app_id)
                elif app_id in dest_app and vuln_id in dest_vuln:  # application vulnerability edge check
                    search_result = context().car_service.graph_search('application', context().args.CONNECTION_NAME + ':' + app_id)
                    temp = []
                    for car_data in search_result['related']:
                        if 'vulnerability/' in str(deep_get(car_data, ["node", "_id"])) and \
                                deep_get(car_data, ["node", "disclosed_on"]) is None and context().args.CONNECTION_NAME in \
                                deep_get(car_data, ["node", "source"]):
                            temp.append(deep_get(car_data, ["node", "external_id"]))
                    if vuln_id not in temp:
                        update_data['app_vuln_edge'].append(value)
                    temp_vuln.add(vuln_id)
                    temp_app.add(app_id)

            for cve in set(temp_vuln):
                dest_vuln.remove(cve)
            for app in set(temp_app):
                dest_app.remove(app)

            for vuln in dest_vuln:  # disabling edges
                temp = dict()
                temp['from'] = machine_id
                temp['to'] = vuln
                temp['edge_type'] = 'asset_vulnerability'
                self.update_edge.append(temp)

            for applications in dest_app:
                temp = dict()
                temp['from'] = machine_id
                temp['to'] = applications
                temp['edge_type'] = 'asset_application'
                self.update_edge.append(temp)


    def update_edges(self):
        context().logger.info('Disabling edges')
        for edge in self.update_edge:
            if 'last_modified' in edge:
                context().car_service.edge_patch(context().args.CONNECTION_NAME, edge, {"last_modified": edge['last_modified']})
            else:
                context().car_service.edge_patch(context().args.CONNECTION_NAME, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.update_edge))

    def delete_vertices(self):
        """Summary: Delete the Asset."""
        context().logger.info('Deleting vertices')
        asset_delete = []
        # delete Asset
        delete_machine = context().asset_server.get_machine_list(delete=get_n_days_ago(15))
        if delete_machine['value']:
            for asset in delete_machine['value']:
                asset_delete.append(asset['id'])
            if asset_delete:
                context().car_service.delete('asset', asset_delete)
        
        context().logger.info('Deleting vertices done: %s', {
            'asset': len(asset_delete)
        } )

        return asset_delete