import datetime
import re

from car_framework.context import context
from car_framework.data_handler import BaseDataHandler


def timestamp_conv(time_string):
    """ Convert date time to epoch time format """
    if 'T' in time_string:
        time_pattern = "%Y-%m-%dT%H:%M:%S"
    else:
        time_pattern = "%Y-%m-%d %H:%M:%S"
    epoch = datetime.datetime(1970, 1, 1)
    converted_time = int(((datetime.datetime.strptime(str(time_string)[:19],
                                                      time_pattern) - epoch).total_seconds()) * 1000)
    return converted_time


def timestamp_conv_tz(time_string):
    """ Convert UTC date time to epoch time format. """
    time_pattern = "%Y-%m-%dT%H:%M:%S.%f%z"
    if len(time_string) <= 20:
        time_pattern = "%Y-%m-%dT%H:%M:%S%z"
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    converted_time = int(((datetime.datetime.strptime(str(time_string),
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


def has_key(dict_val, keys):
    """ Find the keys are present in the dictionary """
    value = True
    for key in keys:
        if key not in dict_val:
            value = False
    return value


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report
            self.source = {'_key': context().args.source,
                           'name': "Google Cloud Platform", 'description': " Google Cloud Platform services",
                           'product_link': "https://cloud.google.com/"}
            self.report = {'_key': str(self.timestamp), 'timestamp': self.timestamp,
                           'type': 'Google Cloud Platform', 'description': 'Google Cloud Platform reports'}
        return {'source': self.source, 'report': self.report}

    # Handle asset from data source
    def handle_asset(self, asset_id, name, **fields):
        """create asset object"""
        res = {}
        res['name'] = name
        res['external_id'] = asset_id
        for key, value in fields.items():
            if value:
                res[key] = value
        self.add_collection('asset', res, 'external_id')

    def handle_hostname(self, asset_id, host_name):
        """Create hostname object"""
        if host_name:
            res = {}
            res['host_name'] = host_name
            res['_key'] = host_name
            self.add_collection('hostname', res, '_key')
            # asset hostname edge creation
            asset_hostname = {'_from_external_id': asset_id, '_to': host_name}
            self.add_edge('asset_hostname', asset_hostname)

    def handle_application(self, app_id, name, asset_id, **fields):
        """create application object"""
        res = {}
        res['name'] = name
        res['external_id'] = app_id
        for key, value in fields.items():
            # Applications other than OS
            if key == 'is_os' and value is False:
                res[key] = value
            if value:
                res[key] = value
        self.add_collection('application', res, 'external_id')
        if asset_id:
            # asset_application edge
            asset_application = {'_from_external_id': asset_id,
                                 '_to_external_id': app_id}
            self.add_edge('asset_application', asset_application)

    def handle_asset_application(self, asset_id, app_id):
        """asset_application edg"""
        asset_application = {'_from_external_id': asset_id,
                             '_to_external_id': app_id}
        self.add_edge('asset_application', asset_application)

    # Handle ipaddress from data source
    def handle_ipaddress(self, ipaddress, asset_id, location=None, **args):
        """create ipaddress object"""
        res = {}
        res['_key'] = ipaddress
        for key, value in args.items():
            if value:
                res[key] = value
        self.add_collection('ipaddress', res, '_key')
        # asset_ipaddress edge
        asset_ipaddress = {'_from_external_id': asset_id,
                           '_to': res['_key']}
        self.add_edge('asset_ipaddress', asset_ipaddress)
        # ipaddress_geolocation edge
        if location:
            ipaddress_geolocation = {'_from': res['_key'],
                                     '_to_external_id': location}
            self.add_edge('ipaddress_geolocation', ipaddress_geolocation)

    # Handle geolocation from data source
    def handle_geolocation(self, obj, asset_id):
        """create geolocation object"""
        location = deep_get(obj, ['resource', 'location'], None)
        if location:
            res = {'external_id': location, 'region': location}
            self.add_collection('geolocation', res, 'external_id')

            # asset_geolocation edge
            asset_geolocation = {'_from_external_id': asset_id,
                                 '_to_external_id': location
                                 }
            self.add_edge('asset_geolocation', asset_geolocation)

    def handle_vulnerability(self, vuln_id, name, asset_id, **fields):
        """create vulnerability object"""
        res = {}
        res['name'] = name
        res['external_id'] = vuln_id
        for key, value in fields.items():
            if value:
                res[key] = value
        self.add_collection('vulnerability', res, 'external_id')

        # asset_vulnerability edge
        asset_vulnerability = {'_from_external_id': asset_id,
                               '_to_external_id': vuln_id}
        self.add_edge('asset_vulnerability', asset_vulnerability)

    def handle_application_vulnerability(self, app_id, vuln_id):
        """application_vulnerability edge object"""
        application_vulnerability = {'_from_external_id': app_id,
                                     '_to_external_id': vuln_id}
        self.add_edge('application_vulnerability', application_vulnerability)

    # Handle vulnerability from data source
    def handle_scc_vulnerability(self, obj, web_service=[], web_app_domain=None):
        """create vulnerability object from scc findings"""
        for vuln in obj:
            finding = deep_get(vuln, ['finding'])
            name = deep_get(vuln, ['finding', 'canonical_name'])
            if name:
                res = {}
                res['name'] = finding.get('category')
                res['external_id'] = name
                res['description'] = finding.get('description')
                published_on = finding.get('create_time', None)
                if published_on:
                    res['published_on'] = timestamp_conv(str(published_on))
                updated_on = finding.get('event_time', None)
                if updated_on:
                    res['updated_on'] = timestamp_conv(str(updated_on))
                base_score = finding.get('severity')
                if base_score:
                    res['base_score'] = base_score

                self.add_collection('vulnerability', res, 'external_id')
                # asset_application edge
                if deep_get(finding, ['source_properties', 'reproductionUrl']):
                    reproduction_url = deep_get(finding, ['source_properties', 'reproductionUrl'])
                    if web_app_domain and web_app_domain in reproduction_url:
                        for asset in web_service:
                            asset_name = asset.split("/")[-1]
                            if asset_name + '-dot' in reproduction_url:
                                self.add_edge('asset_vulnerability', {'_from_external_id': asset.replace('//', ''),
                                                                      '_to_external_id': res['external_id']
                                                                      })
                else:
                    # asset_vulnerability edge
                    asset_id = finding['resource_name']
                    asset_id = asset_id.replace("//", '')
                    asset_vulnerability = {
                        '_from_external_id': asset_id,
                        '_to_external_id': res['external_id']
                    }
                    self.add_edge('asset_vulnerability', asset_vulnerability)

    def handle_vm_instance_ip(self, obj):
        """Create VM instance ipaddress node and associated edges"""
        network = deep_get(obj, ['resource', 'data', 'networkInterfaces'], [])
        asset_id = deep_get(obj, ['name'])
        asset_id = asset_id.replace(deep_get(obj, ['resource', 'data', 'name']),
                                    deep_get(obj, ['resource', 'data', 'id']))
        asset_id = asset_id.replace("//", '')
        location = deep_get(obj, ['resource', 'location'], [])
        for interface in network:
            region_id = deep_get(interface, ['subnetwork'])
            region_id = re.findall('regions/.*?/', region_id)[0]
            region_id = region_id.split('/')[1]
            # Handling public and private IP address
            for ip in [addr for addr in [deep_get(interface, ['ipv6Address']), deep_get(interface, ['networkIP'])] if
                       addr]:
                self.handle_ipaddress(ip, asset_id, location,
                                      region_id=region_id, access_type="Private")
            if deep_get(interface, ['accessConfigs']):
                for config in deep_get(interface, ['accessConfigs']):
                    if config.get('natIP'):
                        self.handle_ipaddress(config.get('natIP'), asset_id, location,
                                              region_id=region_id, access_type="Public")
            if deep_get(interface, ['ipv6AccessConfigs']):
                for config in deep_get(interface, ['ipv6AccessConfigs']):
                    if config.get('natIP'):
                        self.handle_ipaddress(config.get('natIP'), asset_id, location,
                                              region_id=region_id, access_type="Public")

    def handle_vm_instances(self, obj):
        """ handling VM instance node and edges"""
        for instance in obj:
            asset_id = deep_get(instance, ['name'])
            asset_id = asset_id.replace(deep_get(instance, ['resource', 'data', 'name']),
                                        deep_get(instance, ['resource', 'data', 'id']))
            # remove '//' from name
            asset_id = asset_id.replace('//', '')
            name = deep_get(instance, ['resource', 'data', 'name'])
            res = {'asset_type': instance.get('assetType')}
            # key values are same as node car-schema filelds
            description = deep_get(instance, ['resource', 'data', 'description'])
            if description: res['description'] = description
            res['instance_id'] = deep_get(instance, ['resource', 'data', 'id'])
            self.handle_asset(asset_id, name, **res)
            host_name = deep_get(instance, ['resource', 'data', 'hostname'])
            if not host_name:
                host_name = deep_get(instance, ['resource', 'data', 'name'])
            self.handle_hostname(asset_id, host_name)
            self.handle_vm_instance_ip(instance)
            self.handle_geolocation(instance, asset_id)

    def handle_os_application(self, obj, asset_id):
        """Operating system as application"""
        external_id = deep_get(obj, ['osInventory', 'osInfo', 'kernelVersion'])
        name = deep_get(obj, ['osInventory', 'osInfo', 'longName'])
        self.handle_application(external_id, name, asset_id, is_os=True)

    def handle_sw_pkg_application(self, obj, asset_id):
        """Software package as application"""
        packages = obj['osInventory']['items']
        for item in packages.keys():
            app_id = item.split('-', 1)[1]
            name = app_id.split(':', 1)[0]
            self.handle_application(app_id, name, asset_id, is_os=False)

    def handle_vm_software_pkgs(self, obj):
        """ handling VM instance software packages.
            Create application node for os and software packages """
        for instance in obj:
            asset_name = deep_get(instance, ['name'])
            asset_id = re.findall('instances/.*?/', deep_get(instance, ['osInventory', 'name']))
            asset_id = asset_id[0][:-1]
            asset_id = re.sub('instances/.*', asset_id, asset_name)
            # remove '//' from name
            asset_id = asset_id.replace("//", '')
            # OS as application
            self.handle_os_application(instance, asset_id)
            # software package as application
            if deep_get(instance, ['osInventory', 'items']):
                self.handle_sw_pkg_application(instance, asset_id)

    def handle_app_vuln(self, vuln, asset_id):
        """Vulnerable application handling"""
        for vulnerability in deep_get(vuln, ['resource', 'data', 'vulnerabilities']):
            vuln_id = deep_get(vulnerability, ['details', 'cve'])
            for app in deep_get(vulnerability, ['installedInventoryItemIds']):
                app_id = app.split('-', 1)[1]
                app_name = app_id.split(':', 1)[0]
                vuln_name = app_name + ':' + vuln_id
                # Additional fields for vulnerability node
                node = {}
                node['description'] = deep_get(vulnerability, ['details', 'description'])
                node['base_score'] = deep_get(vulnerability, ['details', 'cvssV3', 'baseScore'])
                node['xfr_cvss2_base'] = deep_get(vulnerability, ['details', 'cvssV2Score'])
                node['xfr_cvss3_base'] = deep_get(vulnerability, ['details', 'cvssV3', 'baseScore'])
                self.handle_vulnerability(vuln_id, vuln_name, asset_id, **node)
                self.handle_application_vulnerability(app_id, vuln_id)

    def handle_vm_vulnerabilities(self, obj, project):
        """ handling VM instance vulnerabilities"""
        for vuln in obj:
            # skipping if no vulnerability information available
            if not deep_get(vuln, ['resource', 'data']):
                continue
            # Construct asset_id from vulnerability report
            asset_name = deep_get(vuln, ['resource', 'data', 'name'])
            asset_name = re.sub('projects/.*?/', 'projects/' + project + '/', asset_name)
            asset_id = re.sub('/vulnerabilityReport*', '', asset_name)
            asset_id = re.sub('locations', 'zones', asset_id)
            asset_id = "compute.googleapis.com/" + asset_id
            # OS as application
            if deep_get(vuln, ['resource', 'data', 'vulnerabilities']):
                self.handle_app_vuln(vuln, asset_id)

    def handle_web_app_services(self, obj, web_app=None):
        """Handle web application services"""
        for service in obj:
            asset_id = service['name'].replace('//', '')
            name = deep_get(service, ['resource', 'data', 'id'])
            resource_type = deep_get(service, ['assetType'])
            self.handle_asset(asset_id, name, asset_type=resource_type)
            if web_app:
                # service DNS name is in format of '<service name>-dot-<default domain name>'
                host_name = name + '-dot-' + deep_get(web_app[0], ['resource', 'data', 'defaultHostname'])
                if name == 'default':
                    host_name = deep_get(web_app[0], ['resource', 'data', 'defaultHostname'])
                self.handle_geolocation(web_app[0], asset_id)
                self.handle_hostname(asset_id, host_name)

    def handle_web_app_service_versions(self, obj):
        """Handle web app service versions"""
        for version in obj:
            external_id = deep_get(version, ['name']).replace('//', '')
            name = deep_get(version, ['resource', 'data', 'id'])
            asset_id = deep_get(version, ['resource', 'parent']).replace('//', '')
            # other application fields
            fields = {}
            fields['is_os'] = False
            fields['app_type'] = deep_get(version, ['assetType'])
            fields['status'] = deep_get(version, ['resource', 'data', 'servingStatus'])
            fields['runtime'] = deep_get(version, ['resource', 'data', 'runtime'])
            fields['environment'] = deep_get(version, ['resource', 'data', 'env'])
            self.handle_application(external_id, name, asset_id, **fields)
