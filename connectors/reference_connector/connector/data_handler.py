import datetime, re
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler, JsonField


# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'vulnerabilities' : 'customvulnerability', 'sites' : 'site', 'assets' : 'asset', 'ip_addresses' : 'ipaddress',
    'mac_addresses' : 'macaddress', 'hosts' : 'hostname', 'apps' : 'application', 'ports' : 'port'}

vertices_owning_edges = {
    'asset': ['asset_vulnerability', 'site_asset'],
    'ipaddress': ['asset_ipaddress'],
    'macaddress': ['asset_macaddress'],
    'hostname': ['asset_hostname'],
    'application': ['application_vulnerability'],
    'port': ['application_port', 'ipaddress_port'],
}    

# helper functions
def extract_id(url):
    m = re.search(r'/(\d+)/$', url)
    return int(m.group(1))


def find_by_id(collection, url):
    id = extract_id(url)
    for obj in collection:
        if obj['pk'] == id:
            return obj


def filter_out(source, *fields):
    res = {}
    for key in source.keys():
        if not key in fields:
            res[key] = str(source[key])
    return res


class DataHandler(BaseDataHandler):
    
    xrefproperties = []
    def __init__(self):
        super().__init__()


    # Copies the source object to CAR data model object if attribute have same name
    def copy_fields(self, obj, *fields):
        res = {}
        for field in fields:
            res[field] = obj[field]
        return res


    def car_id(self, collection, source_db_id):
        if collection == 'ipaddress': return context().args.source + '/0/' + str(source_db_id)
        else: return context().args.source + '/' + str(source_db_id)


    def car_ids(self, collection, source_db_ids):
        return list(map(lambda item: self.car_id(collection, item), source_db_ids))


    # Handlers
    # Each endpoint defined in the above endpoint_mapping object should have a handle_* method

    # Create vulnerability Object as per CAR data model from data source
    def handle_vulnerabilities(self, obj):
        res = self.copy_fields(obj, 'name', 'published_on', 'disclosed_on', 'updated_on', 'base_score', )
        res['source'] = context().args.source
        res['reported_at'] = context().report_time
        res['external_id'] = str(obj['pk'])
        res['id'] = self.car_id('customvulnerability', obj['pk'])

        properties = {}
        properties['vcvssbmid'] = str(obj['vcvssbmid'])
        res['properties'] = JsonField(properties)

        xref_properties = []
        for xref in obj['xref_properties']:
            xref_properties.append(filter_out(find_by_id(self.xrefproperties, xref), 'pk'))
        res['xref_properties'] = JsonField(xref_properties)

        self.add_item_to_collection('customvulnerability', res)
        return res['id']

    # Create asset Object as per CAR data model from data source
    def handle_assets(self, obj):
        res = self.copy_fields(obj, 'name', 'initial_value', )
        source = context().args.source
        res['source'] = source
        res['reported_at'] = context().report_time
        res['external_id'] = str(obj['pk'])
        res['id'] = self.car_id('asset', obj['pk'])

        res['asset_type'] = str(obj['type'])

        for vuln in obj.get('vulnerabilities', []):
            self.add_edge('asset_vulnerability', {'asset_id': res['id'], 'vulnerability_id': self.car_id('customvulnerability', extract_id(vuln))})

        if (obj.get('site')):
            self.add_edge('site_asset', {'site_id': self.car_id('site', extract_id(obj['site'])), 'asset_id': res['id']})

        self.add_item_to_collection('asset', res)
        return res['id']

    # Create ipaddress Object as per CAR data model from data source
    def handle_ip_addresses(self, obj):
        res = {}
        address = str(obj['address'])
        source = context().args.source
        res['source'] = source
        res['reported_at'] = context().report_time
        res['external_id'] = '0/' + address
        res['connecting_id'] = '0/' + address
        res['name'] = address
        res['id'] = self.car_id('ipaddress', address)
        res['region_id'] = '0'
        self.add_edge('asset_ipaddress', {'asset_id': self.car_id('asset', extract_id(obj['asset'])), 'ipaddress_id': res['id']})
        self.add_item_to_collection('ipaddress', res)
        return res['id']

    # Create mac address Object as per CAR data model from data source
    def handle_mac_addresses(self, obj):
        res = {}
        source = context().args.source
        res['source'] = source
        res['reported_at'] = context().report_time
        res['external_id'] = str(obj['address'])
        res['id'] = self.car_id('macaddress', obj['pk'])

        res['name'] = str(obj['address'])
        res['connecting_id'] = str(obj['address'])
        self.add_edge('asset_macaddress', {'asset_id': self.car_id('asset', extract_id(obj['asset'])), 'macaddress_id': res['id']})
        self.add_item_to_collection('macaddress', res)
        return res['id']

    # Create hostname Object as per CAR data model from data source
    def handle_hosts(self, obj):
        res = {}
        source = context().args.source
        res['source'] = source
        res['reported_at'] = context().report_time
        res['external_id'] = str(obj['host'])
        res['id'] = self.car_id('hostname', obj['pk'])

        res['name'] = str(obj['host'])
        res['connecting_id'] = str(obj['host'])
        self.add_edge('asset_hostname', {'asset_id': self.car_id('asset', extract_id(obj['asset'])), 'hostname_id': res['id']})
        self.add_item_to_collection('hostname', res)
        return res['id']

    # Create application Object as per CAR data model from data source
    def handle_apps(self, obj):
        res = self.copy_fields(obj, 'name', )
        source = context().args.source
        res['source'] = source
        res['reported_at'] = context().report_time
        res['external_id'] = str(obj['pk'])
        res['id'] = self.car_id('application', obj['pk'])

        for asset_url in obj.get('assets', []):
            asset = context().asset_server.get_object(asset_url)
            for vuln in asset.get('vulnerabilities', []):
                self.add_edge('application_vulnerability', {'application_id': res['id'], 'vulnerability_id': self.car_id('customvulnerability', extract_id(vuln))})

        self.add_item_to_collection('application', res)
        return res['id']

    # Create port Object as per CAR data model from data source
    def handle_ports(self, obj):
        res = self.copy_fields(obj, 'port_number', 'protocol', )
        source = context().args.source
        res['source'] = source
        res['reported_at'] = context().report_time
        res['external_id'] = str(obj['pk'])
        res['id'] = self.car_id('port', obj['pk'])

        res['properties'] = {}
        res['properties']['layer7application'] = str(obj['layer7application'])

        for app in obj.get('apps', []):
            self.add_edge('application_port', {'application_id': self.car_id('application', extract_id(app)), 'port_id': res['id']})

        ids = []
        for ip_ref in obj.get('ip_addresses', []):
            ids.append(extract_id(ip_ref))

        for ip in context().asset_server.get_objects('ip_addresses', ids):
            self.add_edge('ipaddress_port', {'ipaddress_id': self.car_id('ipaddress', ip['address']), 'port_id': res['id']})

        self.add_item_to_collection('port', res)
        return res['id']

    def handle_sites(self, obj):
        res = self.copy_fields(obj, 'name', 'address', )
        res['source'] = context().args.source
        res['reported_at'] = context().report_time
        res['external_id'] = str(obj['pk'])
        res['id'] = self.car_id('site', obj['pk'])
        self.add_item_to_collection('site', res)
        return res['id']

    def get_owned_edges(self, vertex_collection):
        return vertices_owning_edges.get(vertex_collection)
