import datetime
from html2text import html2text
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'asset': ['asset', 'ipaddress', 'hostname', 'macaddress', 'account', 'user', 'geo_location'],
     'vulnerability': ['vulnerability', 'application']
     }


def get_report_time():
    """
    Convert current utc time to epoch time
    """
    delta = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


def get_epoch_time(time_obj):
    """
    Convert string format time to epoch time
    parameters:
            time_obj(str): date time in string format
    returns:
            epoch time
    """
    time_obj = datetime.datetime.strptime(time_obj, '%Y-%m-%dT%H:%M:%fZ')
    delta = time_obj - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


def epoch_to_datetime_conv(epoch_time):
    """
    Convert epoch time to date format time
    :param epoch_time: time in epoch
    :return: date(utc format)
    """
    epoch_time = float(epoch_time) / 1000.0
    date_time = datetime.datetime.fromtimestamp(epoch_time).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    return date_time


def deep_get(_dict, keys, default=None):
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict

# Get list of CVE ids from vulnerability knowledgebase
def get_cve_ids(cve_list):
    if isinstance(cve_list, list):
        return ','.join([id['ID'] for id in cve_list])
    return cve_list['ID']


def get_base_score(cvss=None, cvss_v3=None):
    """
    Vulnerability CVSS score, if vulnerability has both CVSS and CVSS_V3 scores
    the highest value considered as base score
    """
    base_score = 0
    cvss_score = 0
    cvss_v3_score = 0
    if cvss:
        if deep_get(cvss, ['BASE', '#text']):
            cvss_score = float(deep_get(cvss, ['BASE', '#text']))
        else:
            cvss_score = float(deep_get(cvss, ['BASE']))
    if cvss_v3:
        if deep_get(cvss_v3, ['BASE', '#text']):
            cvss_v3_score = float(deep_get(cvss_v3, ['BASE', '#text']))
        else:
            cvss_v3_score = float(deep_get(cvss_v3, ['BASE']))
    if cvss and cvss_v3:
        base_score = max(cvss_score, cvss_v3_score)
    elif cvss:
        base_score = cvss_score
    else:
        base_score = cvss_v3_score
    return base_score


def update_vuln_node_with_kb(node, kb_data):
    """
    Updating vulnerability node with, vulnerability knowledgebase information.
    param
        node: vulnerability vertices(dict)
        kb_data: vulnerability knowledgebase information(dict)
    return:
    """
    # Updating base-score from cvss score
    if deep_get(kb_data, ['CVSS']) or deep_get(kb_data, ['CVSS_V3']):
        score = get_base_score(cvss=deep_get(kb_data, ['CVSS']),
                               cvss_v3=deep_get(kb_data, ['CVSS_V3']))
        node['base_score'] = score
    # Adding additional fields
    for key in ['TITLE', 'CVE_LIST', 'DIAGNOSIS', 'CONSEQUENCE', 'SOLUTION', 'CVSS', 'CVSS_V3']:
        if deep_get(kb_data, [key]):
            if key == 'CVE_LIST':
                node['cve_ids'] = get_cve_ids(kb_data[key]['CVE'])
            elif key == 'TITLE':
                node['name'] = kb_data[key]
            elif key == 'CVSS' or key == 'CVSS_V3':
                ref = 'xfr_cvss2_base'
                if key == 'CVSS_V3':
                    ref = 'xfr_cvss3_base'
                if deep_get(kb_data[key], ['BASE', '#text']):
                    node[ref] = float(deep_get(kb_data[key], ['BASE', '#text']))
                else:
                    node[ref] = float(deep_get(kb_data[key], ['BASE']))
            else:
                node[key.lower()] = html2text(kb_data[key])


def append_vuln_in_asset(host_list, vulnerability_list, applications_list):
    """
    Appending vulnerability, application response in corresponding asset response.
    param
        host_list: host asset api response(list)
        vulnerability_list: vulnerability api response(list)
        applications_list: list of asset applications
    return: combined response (list)
    """
    records = []
    for host in host_list:
        for host_vuln_list in vulnerability_list:
            # qwebHostId will not be present if Host is terminated
            # Appending vulnerability list to corresponding host
            if 'qwebHostId' in host['HostAsset'] and host['HostAsset']['qwebHostId'] == int(host_vuln_list['ID']):
                vuln_list = deep_get(host_vuln_list, ['DETECTION_LIST', 'DETECTION'], [])
                if vuln_list and not isinstance(vuln_list, list):
                    vuln_list = [vuln_list]                   # change the single record into list
                host['HostAsset']['vmdrVulnList'] = vuln_list
        for host_app_list in applications_list:
            if 'id' in host['HostAsset'] and host['HostAsset']['id'] == int(host_app_list['assetId']):
                if host_app_list.get('softwareListData'):
                    host['HostAsset']['applications'] = host_app_list['softwareListData']['software']
        records.append(host)
    return records


def find_location(asset_location):
    """
    Find the location for different cloud platform using api input
    parameters: asset_location(dict): location details
    returns: location(str): location
    """
    location = ''
    if 'region' in asset_location:  # Aws assets region
        location = asset_location.get('region')
    elif 'location' in asset_location:  # Azure, IBM, OCI assets region
        location = asset_location.get('location')
    elif 'zone' in asset_location:  # GCP assets region
        location = asset_location.get('zone')
    return location


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry
            self.source = {'_key': context().args.source,
                           'name': "Qualys",
                           'description': 'The Qualys Cloud Platform and its powerful Cloud Agent provide organizations'
                                          ' with a single IT, security and compliance solution from prevention '
                                          'to detection to response.',
                           'product_link': " https://www.qualys.com/"}
            self.report = {'_key': str(self.timestamp),
                           'timestamp': self.timestamp,
                           'type': 'Qualys',
                           'description': 'Qualys reports'}
        return {'source': self.source, 'report': self.report}

    # Copies the source object to CAR data model object if attribute have same name
    def copy_fields(self, obj, *fields):
        res = {}
        for field in fields:
            res[field] = obj[field]
        return res

    # Create vulnerability Object as per CAR data model from data source
    def handle_vulnerability(self, obj):
        if obj and 'vmdrVulnList' in obj['HostAsset']:
            for vuln in obj['HostAsset']['vmdrVulnList']:
                res = self.copy_fields(obj, )
                score = int(vuln.get('SEVERITY', 0)) * 2  # converting score range (1-5) into (1-10)
                res['external_id'] = vuln['QID']
                res['name'] = 'Host Instance Vulnerability'
                res['source'] = context().args.source
                res['base_score'] = score
                res['description'] = vuln.get('RESULTS')
                # Update node from vulnerability knowledgebase information
                if deep_get(vuln, [vuln['QID']]):
                    update_vuln_node_with_kb(res, vuln[vuln['QID']])
                self.add_collection('vulnerability', res, 'external_id')

                # asset vulnerability edge creation
                asset_vulnerability = {'_from_external_id': str(obj['HostAsset']['id']),
                                       '_to_external_id': str(vuln['QID']),
                                       'risk_score': score}
                self.add_edge('asset_vulnerability', asset_vulnerability)

    # Create asset Object as per CAR data model from data source
    def handle_asset(self, obj):
        if obj:
            res = self.copy_fields(obj, )
            res['external_id'] = obj['HostAsset']['id']
            res['name'] = obj['HostAsset']['name'].lower()
            res['asset_type'] = obj['HostAsset']['type']
            res['description'] = (" ".join([obj['HostAsset'].get('os', ''), obj['HostAsset'].get('type', '').lower(),
                                           obj['HostAsset'].get('name', '')])).strip()

            res['source'] = context().args.source
            self.add_collection('asset', res, 'external_id')

    # Create ip address Object as per CAR data model from data source
    def handle_ipaddress(self, obj):
        if obj:
            network_interface = obj['HostAsset'].get('networkInterface', {})
            for interface in network_interface.get('list', {}):
                res = self.copy_fields(obj, )
                res['source'] = context().args.source
                res['_key'] = interface['HostAssetInterface']['address']
                self.add_collection('ipaddress', res, '_key')

                # asset ipaddress edge creation
                asset_ipaddress = {'_from_external_id': str(obj['HostAsset']['id']),
                                   '_to': interface['HostAssetInterface']['address']}
                self.add_edge('asset_ipaddress', asset_ipaddress)

                if 'vmdrVulnList' in obj['HostAsset']:
                    for vuln in obj['HostAsset']['vmdrVulnList']:
                        ipaddress_vul = {}
                        ipaddress_vul['_from'] = 'ipaddress/' + interface['HostAssetInterface']['address']
                        ipaddress_vul['_to'] = str(vuln['QID'])
                        self.add_edge('ipaddress_vulnerability', ipaddress_vul)

    # Create mac address Object as per CAR data model from data source
    def handle_macaddress(self, obj):
        if obj:
            network_interface = obj['HostAsset'].get('networkInterface', "")
            if network_interface:
                for interface in network_interface['list']:
                    res = self.copy_fields(obj, )
                    key = interface['HostAssetInterface'].get('macAddress', "")
                    if not key:
                        continue
                    res['_key'] = key
                    res['interface'] = interface['HostAssetInterface'].get('interfaceName', "")

                    self.add_collection('macaddress', res, '_key')

                    # asset mac address edge creation
                    asset_macaddress = {'_from_external_id': str(obj['HostAsset']['id']),
                                        '_to': "macaddress/" + interface['HostAssetInterface'].get('macAddress',
                                                                                                   "")}
                    self.add_edge('asset_macaddress', asset_macaddress)

                    # ip address mac address edge creation
                    ipaddress_mac = {'_from': "ipaddress/" + interface['HostAssetInterface']['address'],
                                     '_to': "macaddress/" + interface['HostAssetInterface'].get('macAddress', "")}
                    self.add_edge('ipaddress_macaddress', ipaddress_mac)

    # Create hostname Object as per CAR data model from data source
    def handle_hostname(self, obj):
        if obj:
            res = self.copy_fields(obj, )
            res['host_name'] = obj['HostAsset']['name'].lower()
            key = obj['HostAsset'].get('dnsHostName', "").lower()

            if key:
                res['_key'] = key
            else:
                res['_key'] = res['host_name']

            self.add_collection('hostname', res, '_key')

            # asset hostname edge creation
            asset_hostname = {'_from_external_id': str(obj['HostAsset']['id']), '_to': 'hostname/' + res['_key']}
            self.add_edge('asset_hostname', asset_hostname)

    # Create application Object as per CAR data model from data source
    def handle_application(self, obj):
        if obj and 'vmdrVulnList' in obj['HostAsset'] and 'applications' in obj['HostAsset']:
            for app in obj['HostAsset']['applications']:
                for vuln in obj['HostAsset']['vmdrVulnList']:
                    if app['productName'].lower() in vuln['RESULTS'].lower():
                        res = self.copy_fields(obj, )
                        res['name'] = app['fullName']
                        res['external_id'] = str(app['id'])
                        self.add_collection('application', res, 'external_id')

                        # asset application edge creation
                        asset_application = {'_from_external_id': str(obj['HostAsset']['id']),
                                             '_to_external_id': str(app['id'])}
                        self.add_edge('asset_application', asset_application)

                        # application vulnerability edge creation
                        application_vulnerability = {'_from_external_id': str(app['id']),
                                                     '_to_external_id': str(vuln['QID'])}
                        self.add_edge('application_vulnerability', application_vulnerability)

    # Create account object as per CAR data model from data source
    def handle_account(self, obj):
        if obj:
            if obj['HostAsset'].get('account'):
                for account in obj['HostAsset']['account']['list']:
                    res = self.copy_fields(obj, )
                    res['external_id'] = account['HostAssetAccount']['username']
                    res['name'] = account['HostAssetAccount']['username']
                    self.add_collection('account', res, 'external_id')

                    # asset account edge creation
                    asset_account = {'_from_external_id': str(obj['HostAsset']['id']),
                                     '_to_external_id': account['HostAssetAccount']['username']}
                    self.add_edge('asset_account', asset_account)

    # Create user object as per CAR data model from data source
    def handle_user(self, obj):
        if obj:
            if obj['HostAsset'].get('account'):
                for account in obj['HostAsset']['account']['list']:
                    res = self.copy_fields(obj, )
                    res['external_id'] = account['HostAssetAccount']['username']
                    self.add_collection('user', res, 'external_id')

                    # user account edge creation
                    user_account = {'_from_external_id': account['HostAssetAccount']['username'],
                                    '_to_external_id': account['HostAssetAccount']['username']}
                    self.add_edge('user_account', user_account)

    # Create geo location object as per CAR data model from data source
    def handle_geo_location(self, obj):
        if obj:
            for row in deep_get(obj, ['HostAsset', 'sourceInfo', 'list'], []):
                for asset_location in row:
                    res = self.copy_fields(obj, )
                    location = find_location(row[asset_location])
                    if not location:
                        continue
                    res['external_id'] = location
                    res['region'] = location

                    self.add_collection('geolocation', res, 'external_id')

                    # asset geolocation edge creation
                    asset_geolocation = {'_from_external_id': str(obj['HostAsset']['id']),
                                         '_to_external_id': location}
                    self.add_edge('asset_geolocation', asset_geolocation)
