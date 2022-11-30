import datetime, re
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler


# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'get_detections_for_target' : ['assets', 'ipaddress', 'ports', 'hostname', 'application']}

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
            self.source = {'_key': context().args.source, 'name': context().args.source, 'description': 'Randori server'}
            self.report = {'_key': str(self.timestamp), 'timestamp' : self.timestamp, 'type': 'Randori server', 'description': 'Randori server'}

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
        res['external_id'] = obj['target_id']
        res['description'] = obj['description']
        res['name'] = "%s, %s, %s" % (obj['vendor'], obj['name'], obj['version'] )
        res['perspective_name'] = obj['perspective_name']
        res['randori_notes'] = obj['randori_notes']
        res['first_seen'] = obj['first_seen'].timestamp()
        res['last_seen'] = obj['last_seen'].timestamp()

        if obj['priority_score'] <= 40:
            res['risk'] = obj['priority_score']/40 * 7
        else:
            res['risk'] = 7 + ((obj['priority_score']-40)/160 * 3)

        if obj['impact_score'] == "Low":
            res['business_value'] = 2
        elif obj['impact_score'] == "Medium":
            res['business_value'] = 5
        elif obj['impact_score'] == "High":
            res['business_value'] = 8
        else:
            res['business_value'] = 0

        self.add_collection('asset', res, 'external_id')

    # Create ipaddress Object as per CAR data model from data source
    def handle_ipaddress(self, obj):
        res = {}
        res['_key'] = str(obj['ip'])
        self.add_edge('asset_ipaddress', {'_from_external_id': obj['target_id'], '_to': 'ipaddress/' + res['_key']})
        self.add_collection('ipaddress', res, '_key')


    # Create hostname Object as per CAR data model from data source
    def handle_hostname(self, obj):
        res = {}
        res['_key'] = str(obj['hostname'])
        res['path'] = obj['path']

        self.add_edge('asset_hostname', {'_from_external_id': obj['target_id'], '_to': 'hostname/' + res['_key']})
        self.add_collection('hostname', res, '_key')

    # Create application Object as per CAR data model from data source
    def handle_application(self, obj):
        res = {}
        res['external_id'] = str(obj['target_id'])
        res['name'] = "%s, %s %s" % (str(obj['vendor']), obj['name'], str(obj['version']))
        
        self.add_edge('asset_application', {'_from_external_id': obj['target_id'], '_to_external_id': 'application/' + res['external_id']})
        self.add_collection('application', res, 'external_id')

    # Create port Object as per CAR data model from data source
    def handle_ports(self, obj):
        res = {}
        res['external_id'] = str(obj['target_id'])
        res['port_number'] = obj['port']
        res['protocol'] = str(obj['protocol'])

        self.add_edge('application_port', {'_from_external_id': obj['target_id'], '_to_external_id': res['external_id']})
        self.add_edge('ipaddress_port', {'_from': 'ipaddress/' + obj['ip'], '_to_external_id': res['external_id']})
        self.add_collection('port', res, 'external_id')

