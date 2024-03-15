import re
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler


# Maps asset-server endpoints to CAR service endpoints
endpoint_mapping = {
    'assets': ['asset', 'ipaddress', 'macaddress', 'application'],
    'applications': ['application'],
    'sensors': ['geolocation'],
    'vulnerability': ['vulnerability']
}


def deep_get(_dict, keys, default=None):
    """ Get the value from dictionary. """
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict


def update_app_with_cpe(applications, software_list):
    "Adds cpe information to applications from the asset software list information"
    for app in applications:
        for cpe in software_list:
            if deep_get(cpe, ['asset_id']) and cpe['asset_id'] == app['asset_id'] \
                    and cpe['human_cpe_version'] == app['version']:
                if cpe['human_cpe_product'] in app['product']:
                    app['cpe'] = cpe['cpe']
                    break
                # Comparing application names by removing special characters
                if re.sub('.|_|-| ', '', cpe['human_cpe_product'].lower()) in \
                        re.sub('.|_|-| ', '', app['product'].lower()):
                    app['cpe'] = cpe['cpe']
                    break


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report
            self.source = {'_key': context().args.CONNECTION_NAME,
                           'name': "Nozomi Networks",
                           'description': "Nozomi Networks asset management and vulnerability services",
                           'product_link': "https://www.nozominetworks.com/"}
            self.report = {'_key': str(self.timestamp), 'timestamp': self.timestamp,
                           'type': 'Nozomi Networks',
                           'description': 'Nozomi Networks asset management and vulnerability reports'}
        return {'source': self.source, 'report': self.report}

    # Handle asset from data source
    def handle_asset(self, asset):
        """Create asset object"""
        if asset:
            res = dict()
            res['external_id'] = deep_get(asset, ['id'])
            res['name'] = deep_get(asset, ['name'])
            res["asset_type"] = deep_get(asset, ['type'])
            res["description"] = deep_get(asset, ['product_name'])
            res['risk'] = deep_get(asset, ['risk'])/10
            res["category"] = deep_get(asset, ['technology_category'])
            res["vendor"] = deep_get(asset, ['vendor'])
            res["last_activity_time"] = deep_get(asset, ['last_activity_time'])
            self.add_collection('asset', res, 'external_id')

    def handle_geolocation(self, asset, location):
        """Create geolocation object"""
        if location:
            res = {}
            latitude = deep_get(location, ['latitude'])
            longitude = deep_get(location, ['longitude'])

            if latitude and longitude:
                res['external_id'] = f"{latitude}:{longitude}"
                res['latitude'] = float(latitude)
                res['longitude'] = float(longitude)
            else:
                res['region'] = deep_get(location, ['country'])
                res['external_id'] = res['region']
            self.add_collection('geolocation', res, 'external_id')

            # asset_geolocation edge
            self.add_edge('asset_geolocation', {'_from_external_id': deep_get(asset,['id']),
                                                '_to_external_id': res['external_id']})
            # ipaddress_geolocation edge
            if asset and deep_get(asset, ['ip']):
                for ipaddress in deep_get(asset, ['ip']):
                    self.add_edge('ipaddress_geolocation', {'_from': ipaddress,
                                                            '_to_external_id': res['external_id']})

    def handle_application(self, app):
        """Create application object"""
        if app:
            if deep_get(app, ['os_or_firmware']):
                app_res = {}
                os_or_firmware = re.sub(r'\s+', ' ', deep_get(app, ['os_or_firmware']))
                app_res["name"] = os_or_firmware
                app_res["external_id"] = os_or_firmware
                app_res["is_os"] = True
                self.add_collection('application', app_res, 'external_id')
                self.add_edge('asset_application', {"_from_external_id": deep_get(app, ['id']),
                                                    "_to_external_id": app_res["external_id"]})
            elif deep_get(app, ['version']) and deep_get(app, ['asset_id']):
                app_res = {}
                app_res["name"] = deep_get(app, ['product'])
                app_res["description"] = f"{deep_get(app, ['product'])} {deep_get(app, ['version'])}"
                app_res["external_id"] = f"{deep_get(app, ['product'])}:{deep_get(app, ['version'])}"
                app_res["is_os"] = False
                if deep_get(app, ['cpe']):
                    app_res["cpe"] = deep_get(app, ['cpe'])
                app_res["status"] = deep_get(app, ['status'])
                self.add_collection('application', app_res, 'external_id')
                self.add_edge('asset_application', {"_from_external_id": deep_get(app, ['asset_id']),
                                                    "_to_external_id": app_res["external_id"]})

    def handle_ipaddress(self, obj):
        """Create ipaddress object"""
        if obj and deep_get(obj, ['ip']):
            for ipaddress in deep_get(obj, ['ip']):
                res = {}
                res["_key"] = ipaddress
                self.add_collection('ipaddress', res, '_key')

                asset_ipaddress = {"_from_external_id": deep_get(obj, ['id']),
                                   "_to": ipaddress}
                self.add_edge('asset_ipaddress', asset_ipaddress)

    def handle_macaddress(self, obj):
        """ Create mac address object"""
        if obj and deep_get(obj, ['mac_address']):
            for mac_address in deep_get(obj, ['mac_address']):
                res = {}
                res["_key"] = mac_address
                self.add_collection('macaddress', res, '_key')

                asset_macaddress = {"_from_external_id": deep_get(obj, ['id']),
                                    "_to":  mac_address}
                self.add_edge('asset_macaddress', asset_macaddress)
        # Handle ipaddress from data source

    def handle_ipaddress_macaddress(self, obj):
        """Create ipaddress_macaddress edge"""
        if obj and (deep_get(obj, ['ip']) and deep_get(obj, ['mac_address'])):
            ipaddress_macaddress = {"_from": deep_get(obj, ['ip']),
                                    "_to": deep_get(obj, ['mac_address'])}
            self.add_edge('ipaddress_macaddress', ipaddress_macaddress)

    def handle_vulnerability(self, vulnerability):
        """Create vulnerability object"""
        if vulnerability:
            res = {}
            res['name'] = deep_get(vulnerability, ['cve'])
            res['external_id'] = deep_get(vulnerability, ['id'])
            res['description'] = deep_get(vulnerability, ['cwe_name'])
            res['base_score'] = deep_get(vulnerability, ['cve_score'])
            if deep_get(vulnerability, ['cve_creation_time']):
                res['published_on'] = deep_get(vulnerability, ['cve_creation_time'])
            if deep_get(vulnerability, ['cve_update_time']):
                res['updated_on'] = deep_get(vulnerability, ['cve_update_time'])
            if deep_get(vulnerability, ['references']):
                res['external_references'] = \
                    ','.join([reference['url'] for reference in deep_get(vulnerability, ['references'])])
            self.add_collection('vulnerability', res, 'external_id')
            # asset_vulnerability edge
            if deep_get(vulnerability, ['asset_id']):
                asset_vulnerability = {'_from_external_id': deep_get(vulnerability, ['asset_id']),
                                       '_to_external_id': res['external_id']}
                self.add_edge('asset_vulnerability', asset_vulnerability)

    def handle_application_vulnerability(self, app_id, vuln_id):
        """Create application_vulnerability object"""
        application_vulnerability = {'_from_external_id': app_id,
                                     '_to_external_id': vuln_id}
        self.add_edge('application_vulnerability', application_vulnerability)

    def handle_nozomi_assets(self, obj, sensors):
        for asset in obj:
            for node in endpoint_mapping['assets']:
                getattr(self, 'handle_' + node)(asset)
            # Check asset associated sensor details for Geo location mappings
            if deep_get(asset, ['appliance_hosts']):
                sensor = deep_get(sensors, [deep_get(asset, ['appliance_hosts'])[0]])
                self.handle_geolocation(asset, sensor)

    def handle_nozomi_nodes(self, nodes):
        for node in nodes:
            self.handle_ipaddress_macaddress(node)

    def handle_nozomi_applications(self, obj):
        for app in obj:
            self.handle_application(app)

    def handle_nozomi_vulnerabilities(self, obj):
        for vuln in obj:
            self.handle_vulnerability(vuln)

    def handle_nozomi_app_vuln(self, application, vulnerability):
        # Filtering the vulnerabilities associated with applications
        app_vuln = {vuln['id']: f"{app['product']}:{app['version']}" for app in application for vuln in vulnerability
                    if app['asset_id'] == vuln['asset_id'] and deep_get(app, ['cpe'])
                    and app['cpe'] in vuln['matching_cpes']}
        for vuln_id, app_id in app_vuln.items():
            self.handle_application_vulnerability(app_id, vuln_id)
