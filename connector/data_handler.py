import datetime, re
from car_framework.context import context


# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'vulnerabilities' : 'vulnerability', 'assets' : 'asset', 'ip_addresses' : 'ipaddress', 
    'mac_addresses' : 'macaddress', 'hosts' : 'hostname', 'apps' : 'application', 'ports' : 'port'}

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

def get_report_time():
    delta = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds

class DataHandler(object):

    def __init__(self, xrefproperties):
        self.edges = {}
        self.xrefproperties = xrefproperties

        now = get_report_time()
        # create source entry and it is compuslory for each imports API call
        self.source = {'_key': context().args.source, 'name': context().args.server, 'description': 'Reference Asset server'}
        self.report = {'_key': str(now), 'timestamp' : now, 'type': 'Reference Asset server', 'description': 'Reference Asset server'}

    # Copies the source object to CAR data model object if attribute have same name
    def copy_fields(self, obj, *fields):
        res = {}
        for field in fields:
            res[field] = obj[field]
        return res

    # Adds the edge between two vertices
    def add_edge(self, name, object):
        objects = self.edges.get(name)
        if not objects:
            objects = []; self.edges[name] = objects
        objects.append(object)

    # Each endpoint defined in the above endpoint_mapping object should have a handle_* method

    # Create vulnerability Object as per CAR data model from data source
    def handle_vulnerabilities(self, obj):
        res = self.copy_fields(obj, 'name', 'published_on', 'disclosed_on', 'updated_on', 'vcvssbmid', 'base_score', )
        res['external_id'] = str(obj['pk'])
        res['vcvssbmid'] = str(obj['vcvssbmid'])
        res['xref_properties'] = []
        for xref in obj['xref_properties']:
            res['xref_properties'].append(filter_out(find_by_id(self.xrefproperties, xref), 'pk'))
        return res

    # Create asset Object as per CAR data model from data source
    def handle_assets(self, obj):
        res = self.copy_fields(obj, 'name', )
        res['external_id'] = str(obj['pk'])
        res['assetid'] = str(obj['pk'])
        res['asset_type'] = str(obj['type'])

        for vuln in obj.get('vulnerabilities', []):
            self.add_edge('asset_vulnerability', {'_from_external_id': res['external_id'], '_to_external_id': str(extract_id(vuln)),
                 'source': context().args.source})

        return res

    # Create ipaddress Object as per CAR data model from data source
    def handle_ip_addresses(self, obj):
        res = {}
        res['_key'] = str(obj['address'])
        self.add_edge('asset_ipaddress', {'_from_external_id': str(extract_id(obj['asset'])), '_to': 'ipaddress/' + res['_key'], 
            'source': context().args.source})
        return res

    # Create mac address Object as per CAR data model from data source
    def handle_mac_addresses(self, obj):
        res = {}
        res['_key'] = str(obj['address'])
        self.add_edge('asset_macaddress', {'_from_external_id': str(extract_id(obj['asset'])), '_to': 'macaddress/' + res['_key'], 
            'source': context().args.source})
        return res

    # Create hostname Object as per CAR data model from data source
    def handle_hosts(self, obj):
        res = {}
        res['_key'] = str(obj['host'])
        self.add_edge('asset_hostname', {'_from_external_id': str(extract_id(obj['asset'])), '_to': 'hostname/' + res['_key'], 
            'source': context().args.source})
        return res

    # Create application Object as per CAR data model from data source
    def handle_apps(self, obj):
        res = self.copy_fields(obj, 'name', )
        res['external_id'] = str(obj['pk'])
        
        for asset_url in obj.get('assets', []):
            asset = context().asset_server.get_object(asset_url)
            for vuln in asset.get('vulnerabilities', []):
                self.add_edge('application_vulnerability', {'_from_external_id': res['external_id'], '_to_external_id': str(extract_id(vuln)),
                    'source': context().args.source})

        return res

    # Create port Object as per CAR data model from data source
    def handle_ports(self, obj):
        res = self.copy_fields(obj, 'port_number', 'layer7application', 'protocol', )
        res['external_id'] = str(obj['pk'])

        for app in obj.get('apps', []):
            self.add_edge('application_port', {'_from_external_id': str(extract_id(app)), '_to_external_id': res['external_id'],
                'source': context().args.source})

        ids = []        
        for ip_ref in obj.get('ip_addresses', []):
            ids.append(extract_id(ip_ref))

        for ip in context().asset_server.get_objects('ip_addresses', ids):
            self.add_edge('ipaddress_port', {'_from': 'ipaddress/' + str(ip['address']), '_to_external_id': res['external_id'],
                'source': context().args.source})

        return res
