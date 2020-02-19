import requests, base64, datetime, json, re
from full_import import FullImport


# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'xrefproperties' : None, 'vulnerabilities' : 'vulnerability', 'assets' : 'asset', 'ip_addresses' : 'ipaddress', 
    'mac_addresses' : 'macaddress', 'hosts' : 'hostname', 'apps' : 'application', 'ports' : 'port'}


def get_report_time():
    delta = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


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


class ExampleFullImport(FullImport):
    def __init__(self, context):
        super().__init__(context)

        auth = base64.encodestring(('%s:%s' % (context.args.username, context.args.password)).encode()).decode().strip()
        self.server_headers = {'Accept' : 'application/json', 'Authorization': 'Basic ' + auth}

        now = get_report_time()
        self.source = {'_key': self.context.source, 'name': self.context.args.server, 'description': 'Reference Asset server'}
        self.report = {'_key': str(now), 'timestamp' : now, 'type': 'Reference Asset server', 'description': 'Reference Asset server'}
        self.source_report = [{'active': True, '_from': 'source/' + self.source['_key'], '_to': 'report/' + self.report['_key'], 'timestamp': self.report['timestamp']}]

        self.report_asset, self.xrefproperties, self.assets, self.asset_macaddress, self.asset_macaddress, self.asset_ipaddress, \
            self.asset_vulnerability, self.report_ipaddress, self.asset_hostname, self.report_application, self.app_port, self.app_vuln, self.ipaddress_port = [], [], [], [], [], [], [], [], [], [], [], [], []

        self.cache = {}


    def _cache(self, endpoint, obj):
        id = obj.get('pk')
        if id:
            self.cache['%s/%s/%s/' % (self.context.args.server, endpoint, id)] = obj


    def get(self, url):
        cached = self.cache.get(url)
        if cached: return cached
        r = requests.get(url, headers=self.server_headers)
        res = r.json()
        self.cache[url] = res
        return res


    def import_collection(self, asset_server_endpoint, name):
        r = requests.get('%s/%s' % (self.context.args.server, asset_server_endpoint), headers=self.server_headers)
        data = []
        for obj in r.json():
            self._cache(asset_server_endpoint, obj)
            res = eval('self.handle_%s(obj)' % asset_server_endpoint.lower())
            if res: data.append(res)
        if name:
            self.send_data(name, data)


    def handle_xrefproperties(self, obj):
        self.xrefproperties.append(obj)


    def copy_fields(self, obj, *fields):
        res = {}
        for field in fields:
            res[field] = obj[field]
        return res


    def handle_vulnerabilities(self, obj):
        res = self.copy_fields(obj, 'name', 'published_on', 'disclosed_on', 'updated_on', 'vcvssbmid', 'base_score', )
        res['external_id'] = str(obj['pk'])
        res['vcvssbmid'] = str(obj['vcvssbmid'])
        res['xref_properties'] = []
        for xref in obj['xref_properties']:
            res['xref_properties'].append(filter_out(find_by_id(self.xrefproperties, xref), 'pk'))
        return res


    def handle_assets(self, obj):
        res = self.copy_fields(obj, 'name', )
        res['external_id'] = str(obj['pk'])
        res['assetid'] = str(obj['pk'])
        res['asset_type'] = str(obj['type'])

        self.report_asset.append({'active': True, 'source': self.context.source, '_from': 'report/' + self.report['_key'], 
            '_to_external_id': res['external_id'], 'timestamp': self.report['timestamp']})

        for vuln in (obj.get('vulnerabilities') or []):
            self.asset_vulnerability.append({'_from_external_id': res['external_id'], '_to_external_id': str(extract_id(vuln)),
                'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})

        return res


    def handle_ip_addresses(self, obj):
        res = {}
        res['external_id'] = str(obj['pk'])
        res['_key'] = str(obj['address'])
        self.asset_ipaddress.append({'_from_external_id': str(extract_id(obj['asset'])), '_to': 'ipaddress/' + res['_key'], 
            'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})
        self.report_ipaddress.append({'_from': 'report/' + self.report['_key'], '_to': 'ipaddress/' + res['_key'], 
            'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})
        return res


    def handle_mac_addresses(self, obj):
        res = {}
        res['external_id'] = str(obj['pk'])
        res['_key'] = str(obj['address'])
        self.asset_macaddress.append({'_from_external_id': str(extract_id(obj['asset'])), '_to': 'macaddress/' + res['_key'], 
            'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})
        return res


    def handle_hosts(self, obj):
        res = {}
        res['external_id'] = str(obj['pk'])
        res['_key'] = str(obj['host'])
        self.asset_hostname.append({'_from_external_id': str(extract_id(obj['asset'])), '_to': 'hostname/' + res['_key'], 
            'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})
        return res


    def handle_apps(self, obj):
        res = self.copy_fields(obj, 'name', )
        res['external_id'] = str(obj['pk'])
        self.report_application.append({'_from': 'report/' + self.report['_key'], '_to_external_id': res['external_id'], 
            'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})

        for asset_url in (obj.get('assets') or []):
            asset = self.get(asset_url)
            for vuln in (asset.get('vulnerabilities') or []):
                self.app_vuln.append({'_from_external_id': res['external_id'], '_to_external_id': str(extract_id(vuln)),
                    'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})

        return res


    def handle_ports(self, obj):
        res = self.copy_fields(obj, 'port_number', 'layer7application', 'protocol', )
        res['external_id'] = str(obj['pk'])

        for app in (obj.get('apps') or []):
            self.app_port.append({'_from_external_id': str(extract_id(app)), '_to_external_id': res['external_id'],
                'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})

        for ip_ref in (obj.get('ip_addresses') or []):
            ip = self.get(ip_ref)
            self.ipaddress_port.append({'_from': 'ipaddress/' + str(ip['address']), '_to_external_id': res['external_id'],
                'timestamp': self.report['timestamp'], 'source': self.context.source, 'report': self.report['_key'], 'active': True})

        return res


    def import_asset_macaddress(self):
        data = []
        for id in self.assets:
            data.append({'active': True, 'source': self.context.source, '_from': 'report/' + self.report['_key'], 
                '_to_external_id': id, 'timestamp': self.report['timestamp']})
        self.send_data('report_asset', data)


    def import_vertices(self):
        for asset_server_endpoint, data_name in endpoint_mapping.items():
            self.import_collection(asset_server_endpoint, data_name)


    def import_edges(self):
        self.send_data('report_asset', self.report_asset)
        self.send_data('asset_macaddress', self.asset_macaddress)
        self.send_data('asset_ipaddress', self.asset_ipaddress)
        self.send_data('asset_vulnerability', self.asset_vulnerability)
        self.send_data('report_ipaddress', self.report_ipaddress)
        self.send_data('asset_hostname', self.asset_hostname)
        self.send_data('report_application', self.report_application)
        self.send_data('application_port', self.app_port)
        self.send_data('application_vulnerability', self.app_vuln)
        self.send_data('ipaddress_port', self.ipaddress_port)
