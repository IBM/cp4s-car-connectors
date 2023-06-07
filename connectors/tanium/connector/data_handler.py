import datetime, re
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

import dateutil.parser as dparser

# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'tanium_endpoints': [
        'assets', 'ipaddresses', 'ports', 'hostname', 'application', 'macaddress', 'account', 'user']
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

def epoch_to_datetime_conv(epoch_time):
    """
    Convert epoch time to date format time
    :param epoch_time: time in epoch
    :return: date(iso format)
    """
    epoch_time = float(epoch_time) / 1000.0
    date_time = datetime.datetime.fromtimestamp(epoch_time).replace(microsecond=0)
    return date_time

class DataHandler(BaseDataHandler):
    xrefproperties = []

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry and it is compuslory for each imports API call
            self.source = {'_key': context().args.CONNECTION_NAME, 'name': context().args.CONNECTION_NAME, 'description': 'Tanium server'}
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
        res['name'] = "%s, %s" % (obj['manufacturer'], obj['name'])
        if obj['eidFirstSeen']:
            res['first_seen'] = dparser.parse(obj['eidFirstSeen']).timestamp()
        if obj['eidLastSeen']:
            res['last_seen'] = dparser.parse(obj['eidLastSeen']).timestamp() 
        if obj['risk'] and obj['risk']['totalScore']:
            res['risk'] = obj['risk']['totalScore'] / 100
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
        for mac in obj['macAddresses']:
            res = {'_key': mac}
            self.add_edge('asset_macaddress', {'_from_external_id': obj['id'], '_to': 'macaddress/' + res['_key']})

            self.add_edge('ipaddress_macaddress',
                          {'_from': 'ipaddress/' + obj['ipAddress'], '_to': 'macaddress/' + res['_key']})
            self.add_collection('macaddress', res, '_key')

    # Create hostname Object as per CAR data model from data source
    def handle_hostname(self, obj):
        res = {}
        res['_key'] = str(obj['domainName'])

        self.add_edge('asset_hostname', {'_from_external_id': obj['id'], '_to': 'hostname/' + res['_key']})
        self.add_collection('hostname', res, '_key')

    def handle_account(self, obj):
        res = {}
        user = obj['primaryUser']
        if user['email']:
            res['external_id'] = str(user['email'])
            res['name'] = user['name']

            self.add_edge('asset_account', {'_from_external_id': obj['id'], '_to_external_id': 'account/' + res['external_id']})
            self.add_collection('account', res, 'external_id')

    
    # Create user Object as per CAR data model from data source
    def handle_user(self, obj):
        res = {}
        user = obj['primaryUser']
        if user['email']:
            res['external_id'] = str(user['email'])
            res['fullname'] = user['name']
            res['email'] = user['email']
            res['department'] = user['department']

            self.add_edge('user_account', {'_from_external_id': res['external_id'], '_to_external_id': 'account/' + res['external_id']})
            self.add_collection('user', res, 'external_id')

    # Create application Object as per CAR data model from data source
    def handle_application(self, obj):
        # Import OS
        os = obj['os']
        res = {}
        res['external_id'] = str(os['name'])
        res['name'] = os['name']
        res['is_os'] = True
        self.add_edge('asset_application',
                        {'_from_external_id': obj['id'], '_to_external_id': 'application/' + res['external_id']})
        self.add_collection('application', res, 'external_id')
        
        # Import deployedSoftwarePackages
        for package in obj['deployedSoftwarePackages']:
            res = {}
            res['external_id'] = package['id']
            res['name'] = package['vendor']
            res['description'] = "%s: %s" % (package['vendor'], package['version'])
            res['app_type'] = "SoftwarePackages"
            self.add_edge('asset_application',
                          {'_from_external_id': obj['id'], '_to_external_id': 'application/' + res['external_id']})
            self.add_collection('application', res, 'external_id')

        # Import installedApplications
        for app in obj['installedApplications']:
            res = {}
            res['external_id'] = str(app['name'])
            res['name'] = app['name']
            res['description'] = "%s: %s" % (app['name'], app['version'])
            res['app_type'] = "application"
            self.add_edge('asset_application',
                          {'_from_external_id': obj['id'], '_to_external_id': 'application/' + res['external_id']})
            self.add_collection('application', res, 'external_id')

        # Import services
        for svc in obj['services']:
            res = {}
            res['external_id'] = str(obj['name'])
            res['name'] = svc['displayName']
            res['status'] = svc['status']
            res['app_type'] = "services"
            self.add_edge('asset_application',
                          {'_from_external_id': obj['id'], '_to_external_id': 'application/' + res['external_id']})
            self.add_collection('application', res, 'external_id')

    # Create port Object as per CAR data model from data source
    def handle_ports(self, obj):
        res = {}
        res['external_id'] = str(obj['id'])
        for port in obj['discover']['openPorts']:
            res['port_number'] = port
            res['protocol'] = "N/A"
            self.add_edge('application_port',
                          {'_from_external_id': obj['id'], '_to_external_id': res['external_id']})
            self.add_edge('ipaddress_port',
                          {'_from': 'ipaddress/' + obj['ipAddress'], '_to_external_id': res['external_id']})
            self.add_collection('port', res, 'external_id')
