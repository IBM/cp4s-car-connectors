import datetime, re
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'tanium_endpoints': [
        'assets', 'ipaddress', 'ipaddresses', 'ports', 'hostname', 'application', 'macaddress']
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


def get_report_time():
    delta = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


class DataHandler(BaseDataHandler):
    xrefproperties = []

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry and it is compuslory for each imports API call
            self.source = {'_key': context().args.source, 'name': context().args.source, 'description': 'Tanium server'}
            self.report = {'_key': str(self.timestamp), 'timestamp': self.timestamp, 'type': 'Tanium server',
                           'description': 'Tanium server'}

        return {'source': self.source, 'report': self.report}

    # Copies the source object to CAR data model object if attribute have same name
    def copy_fields(self, obj, *fields):
        res = {}
        for field in fields:
            res[field] = obj[field]
        return res

    # Create asset Object as per CAR data model from data source
    def handle_assets(self, obj):
        res = {}
        res['external_id'] = obj['id']
        if obj['manufacturer']:
            res['name'] = "%s, %s" % (obj['manufacturer'], obj['name'])
        else:
            res['name'] = obj['name']
        res['first_seen'] = obj['eidFirstSeen']
        res['last_seen'] = obj['eidLastSeen']

        if obj['risk']['totalScore'] <= 40:
            res['risk'] = obj['risk']['totalScore'] / 40 * 7
        else:
            res['risk'] = 7 + ((obj['risk']['totalScore'] - 40) / 160 * 3)

        self.add_collection('asset', res, 'external_id')

    # Create ipaddress Object as per CAR data model from data source
    def handle_ipaddress(self, obj):
        res = {'_key': str(obj['ipAddress'])}
        self.add_edge('asset_ipaddress', {'_from_external_id': obj['id'], '_to': 'ipaddress/' + res['_key']})
        self.add_collection('ipaddress', res, '_key')

    # Create ipaddress Object as per CAR data model from data source
    def handle_ipaddresses(self, obj):
        for ip in obj['ipAddresses']:
            res = {'_key': str(ip)}
            self.add_edge('asset_ipaddress', {'_from_external_id': obj['id'], '_to': 'ipaddress/' + res['_key']})
            self.add_collection('ipaddress', res, '_key')

    def handle_macaddress(self, obj):
        res = {}
        key = obj.get('macAddresses', "")
        res['_key'] = key
        self.add_collection('macaddress', res, '_key')

        # asset mac address edge creation
        asset_macaddress = {'_from_external_id': str(obj['id']),
                            '_to': "macaddress/" + obj.get('macAddress', "")}
        self.add_edge('asset_macaddress', asset_macaddress)

        # ip address mac address edge creation
        for ip in obj['ipAddresses']:
            ipaddress_mac = {'_from': "ipaddress/" + ip,
                             '_to': "macaddress/" + obj.get('macAddress', "")}
            self.add_edge('ipaddress_macaddress', ipaddress_mac)

    # Create hostname Object as per CAR data model from data source
    def handle_hostname(self, obj):
        res = {}
        res['_key'] = str(obj['name'])

        self.add_edge('asset_hostname', {'_from_external_id': obj['id'], '_to': 'hostname/' + res['_key']})
        self.add_collection('hostname', res, '_key')

    # Create application Object as per CAR data model from data source
    def handle_application(self, obj):
        # pass
        res = {}
        res['external_id'] = str(obj['id'])
        for svc in obj['services']:
            res['name'] = svc['name']
            self.add_edge('asset_application',
                          {'_from_external_id': obj['id'], '_to_external_id': 'application/' + res['external_id']})
            self.add_collection('application', res, 'external_id')

    # Create port Object as per CAR data model from data source
    def handle_ports(self, obj):
        res = {}
        res['external_id'] = str(obj['id'])
        for port in obj['discover']['openPorts']:
            res['port_number'] = port
            self.add_edge('application_port',
                          {'_from_external_id': obj['id'], '_to_external_id': res['external_id']})
            self.add_edge('ipaddress_port',
                          {'_from': 'ipaddress/' + obj['ipAddress'], '_to_external_id': res['external_id']})
            self.add_collection('port', res, 'external_id')
