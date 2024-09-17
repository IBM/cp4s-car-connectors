
import datetime

from car_framework.context import context
from car_framework.data_handler import BaseDataHandler


def timestamp_conv(time_string):
    """ Convert date time to epoch time format """
    converted_time = None
    if time_string:
        if 'T' in time_string:
            time_pattern = "%Y-%m-%dT%H:%M:%S"
        else:
            time_pattern = "%Y-%m-%d %H:%M:%S"
        epoch = datetime.datetime(1970, 1, 1)
        converted_time = int(((datetime.datetime.strptime(str(time_string)[:19],
                                                        time_pattern) - epoch).total_seconds()) * 1000)
    return converted_time


def epoch_to_datetime_conv(epoch_time):
    """
    Convert epoch time to date format time
    :param epoch_time: time in epoch
    :return: date(utc format)
    """
    epoch_time = float(epoch_time) / 1000.0
    date_time = datetime.datetime.fromtimestamp(epoch_time, datetime.timezone.utc).replace(microsecond=0) \
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    return date_time


def deep_get(_dict, keys, default=None):
    """ Get the value from dictionary. """
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict


def group_host_sensor_apps(applications):
    """Group the agent related applications from all applications"""
    group_apps = {}
    for app in applications:
        agent_id = deep_get(app, ['host', 'aid'])
        if agent_id in group_apps.keys():
            group_apps[agent_id].append(app)
        else:
            group_apps[agent_id] = list()
            group_apps[agent_id].append(app)
    return group_apps

def remove_duplicates(items):
    """Remove any duplicate hosts from the array of hosts"""
    context().logger.debug("Removing duplicates from list with length: %s", len(items))
    unique_items = []
    for item in items:
        if item not in unique_items:
            unique_items.append(item)
    context().logger.debug("Returning %s unique items", len(unique_items))
    return unique_items

class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report
            self.source = {'_key': context().args.CONNECTION_NAME,
                           'name': "CrowdStrike Falcon",
                           'description': " CrowdStrike Falcon asset discovery and vulnerability services",
                           'product_link': "https://crowdstrike.com/"}
            self.report = {'_key': str(self.timestamp), 'timestamp': self.timestamp,
                           'type': 'CrowdStrike Falcon',
                           'description': 'CrowdStrike Falcon asset discovery and vulnerability reports'}
        return {'source': self.source, 'report': self.report}

    # Handle asset from data source
    def handle_asset(self, obj):
        """create asset object"""
        for host in obj:
            res = dict()
            if deep_get(host, ['entity_type']) in ['unsupported', 'unmanaged']:
                res['external_id'] = deep_get(host, ['id'])
                res['name'] = deep_get(host, ['entity_type']) + ':' + deep_get(host, ['id'])
                res["last_seen_timestamp"] = timestamp_conv(deep_get(host, ['last_seen_timestamp']))
                self.add_collection('asset', res, 'external_id')
                self.handle_ipaddress(host)
                self.handle_macaddress(deep_get(host, ['network_interfaces']))
            else:
                res["name"] = deep_get(host, ['hostname'])
                res["external_id"] = deep_get(host, ['id'])
                res["asset_type"] = deep_get(host, ['system_product_name'])
                res["description"] = deep_get(host, ['product_type_desc'])
                res["last_seen_timestamp"] = timestamp_conv(deep_get(host, ['last_seen_timestamp']))
                res["agent_id"] = deep_get(host, ['aid'])
                self.add_collection('asset', res, 'external_id')

                self.handle_hostname(deep_get(host, ['hostname']))
                self.handle_ipaddress(host)
                self.handle_macaddress(deep_get(host, ['network_interfaces']))
                self.handle_geolocation(deep_get(host, ['city']), deep_get(host, ['country']))

                os_res = {}
                os_res["name"] = deep_get(host, ['os_version'])
                os_res["external_id"] = deep_get(host, ['os_version']) + "/" + \
                                        deep_get(host, ['kernel_version'])
                os_res["is_os"] = True
                self.add_collection('application', os_res, 'external_id')

                asset_application = {"_from_external_id": deep_get(host, ['id']),
                                     "_to_external_id": deep_get(host, ['os_version']) + "/" +
                                                        deep_get(host, ['kernel_version'])}
                self.add_edge('asset_application', asset_application)

                asset_hostname = {"_from_external_id": deep_get(host, ['id']),
                                  "_to": deep_get(host, ['hostname'])}
                self.add_edge('asset_hostname', asset_hostname)

                asset_geolocation = {"_from_external_id": deep_get(host, ['id']),
                                     "_to_external_id": deep_get(host, ['city']) + ", " + deep_get(host, ['country'])}
                self.add_edge('asset_geolocation', asset_geolocation)

    def handle_hostname(self, hostname):
        """Create hostname object"""
        res = {}
        res["host_name"] = hostname
        res["external_id"] = hostname
        self.add_collection('hostname', res, 'external_id')

    def handle_application(self, obj):
        """create application object"""
        for app in obj:
            if deep_get(app, ['name']):
                app_res = {}
                app_res["name"] = deep_get(app, ['name'])
                app_res["external_id"] = deep_get(app, ['id'])
                app_res["is_os"] = False
                if deep_get(app, ['vendor']):
                    app_res["owner"] = deep_get(app, ['vendor'])
                app_res["last_access_time"] = timestamp_conv(deep_get(app, ['last_used_timestamp']) or
                                                             deep_get(app, ['last_updated_timestamp']))
                self.add_collection('application', app_res, 'external_id')

            asset_application = {"_from_external_id": deep_get(app, ['host', 'id']),
                                 "_to_external_id": deep_get(app, ['id'])}
            self.add_edge('asset_application', asset_application)

    # Handle ipaddress from data source
    def handle_ipaddress(self, obj):
        """create ipaddress object"""
        if deep_get(obj, ['external_ip']):
            ext_res = {}
            ext_res["_key"] = deep_get(obj, ['external_ip'])
            ext_res["region_id"] = deep_get(obj, ['city']) + ", " + deep_get(obj, ['country'])
            self.add_collection('ipaddress', ext_res, '_key')

            ipaddress_geolocation = {"_from": deep_get(obj, ['external_ip']),
                                     "_to_external_id": deep_get(obj, ['city']) + ", " + deep_get(obj, ['country'])}
            self.add_edge('ipaddress_geolocation', ipaddress_geolocation)

            ipaddress_hostname = {"_from": deep_get(obj, ['external_ip']),
                                  "_to": deep_get(obj, ['hostname'])}
            self.add_edge('ipaddress_hostname', ipaddress_hostname)

            asset_ipaddress = {"_from_external_id": deep_get(obj, ['id']),
                               "_to": deep_get(obj, ['external_ip'])}
            self.add_edge('asset_ipaddress', asset_ipaddress)

        for network in deep_get(obj, ['network_interfaces']):
            int_res = {}
            int_res["_key"] = deep_get(network, ['local_ip'])
            if deep_get(obj, ['city']):
                int_res["region_id"] = deep_get(obj, ['city']) + ", " + deep_get(obj, ['country'])
            self.add_collection('ipaddress', int_res, '_key')

            asset_ipaddress = {"_from_external_id": deep_get(obj, ['id']),
                               "_to": deep_get(network, ['local_ip'])}
            self.add_edge('asset_ipaddress', asset_ipaddress)
            if deep_get(obj, ['city']):
                ipaddress_geolocation = {"_from": deep_get(network, ['local_ip']),
                                         "_to_external_id": deep_get(obj, ['city']) + ", " + deep_get(obj, ['country'])}
                self.add_edge('ipaddress_geolocation', ipaddress_geolocation)
            if deep_get(obj, ['hostname']):
                ipaddress_hostname = {"_from": deep_get(network, ['local_ip']),
                                      "_to": deep_get(obj, ['hostname'])}
                self.add_edge('ipaddress_hostname', ipaddress_hostname)

            asset_macaddress = {"_from_external_id": deep_get(obj, ['id']),
                                "_to": deep_get(network, ['mac_address']).replace('-', ':')}
            self.add_edge('asset_macaddress', asset_macaddress)

            ipaddress_macaddress = {"_from": deep_get(network, ['local_ip']),
                                    "_to": deep_get(network, ['mac_address']).replace('-', ':')}
            self.add_edge('ipaddress_macaddress', ipaddress_macaddress)
            if deep_get(obj, ['external_ip']):
                ipaddress_macaddress = {"_from": deep_get(obj, ['external_ip']),
                                        "_to": deep_get(network, ['mac_address']).replace('-', ':')}
                self.add_edge('ipaddress_macaddress', ipaddress_macaddress)

    def handle_macaddress(self, network_int):
        for network in network_int:
            res = {}
            res["_key"] = deep_get(network, ['mac_address']).replace('-', ':')
            if deep_get(network, ['interface_alias']):
                res["interface"] = deep_get(network, ['interface_alias'])
            self.add_collection('macaddress', res, '_key')

    # Handle geolocation from data source
    def handle_geolocation(self, city, country):
        """create geolocation object"""
        res = {}
        res["region"] = city + ", " + country
        res["external_id"] = city + ", " + country
        self.add_collection('geolocation', res, 'region')

    def handle_account(self, obj):
        """ Account object creation"""
        for account in obj:
            res = {}
            res["name"] = deep_get(account, ['account_name'])
            res["external_id"] = deep_get(account, ['account_id'])
            res["last_successful_login_time"] = timestamp_conv(deep_get(account, ['login_timestamp']))
            self.add_collection('account', res, 'external_id')
            self.handle_user(deep_get(account, ['username']))

            user_account = {"_from_external_id": deep_get(account, ['username']),
                            "_to_external_id": deep_get(account, ['account_id'])}
            self.add_edge('user_account', user_account)
            asset_account = {"_from_external_id": deep_get(account, ['host_id']),
                             "_to_external_id": deep_get(account, ['account_id'])}
            self.add_edge('asset_account', asset_account)

    def handle_user(self, obj):
        """User object creation"""
        res = {}
        res["username"] = obj
        res["external_id"] = obj
        self.add_collection('user', res, 'external_id')

    def handle_vulnerability(self, obj, agent_related_asset_ids):
        """create vulnerability object"""
        for vulnerability in obj:
            agent_id = deep_get(vulnerability, ['aid'])
            res = {}
            res['name'] = deep_get(vulnerability, ['cve', 'id'])
            res['external_id'] = deep_get(vulnerability, ['cve', 'id'])
            res['description'] = deep_get(vulnerability, ['cve', 'description'])
            res['base_score'] = deep_get(vulnerability, ['cve', 'base_score'])
            res['xfr_wx'] = deep_get(vulnerability, ['cve', 'exploitability_score'])
            res['published_on'] = timestamp_conv(deep_get(vulnerability, ['cve', 'published_date']))
            self.add_collection('vulnerability', res, 'external_id')
            # Vulnerability related edges
            # asset_vulnerability
            asset_vulnerability = {'_from_external_id': agent_related_asset_ids[agent_id],
                                   '_to_external_id': res['external_id']}
            self.add_edge('asset_vulnerability', asset_vulnerability)
            # application_vulnerability
            for app in vulnerability['apps']:
                if deep_get(app, ['app_id']):
                    self.add_edge('application_vulnerability', {'_from_external_id': deep_get(app, ['app_id']),
                                                                '_to_external_id': res['external_id']})
