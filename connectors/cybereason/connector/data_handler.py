import time
import datetime
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = {
        'asset': ['asset', 'hostname', 'application', 'ipaddress', 'macaddress'],
        'vulnerability': ['vulnerability']
    }


def get_report_time():
    """
    Convert current utc time to epoch time
    """
    delta = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


def get_current_epoch_time():
    """returns: current time in millisec"""
    return round(time.time() * 1000)


def get_vulnerability_score(severity_level):
    """
    Returns vulnerability score based on the severity level
    """
    if severity_level == "HIGH":
        score = 8
    elif severity_level == "MEDIUM":
        score = 5
    else:
        score = 2
    return score


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry
            self.source = {'_key': context().args.source,
                           'name': "Cybereason",
                           'description': 'The Cybereason platform provides military-grade cyber security'
                                          'with real-time awareness and detection',
                           'product_link': "https://www.cybereason.com"}
            self.report = {'_key': str(self.timestamp),
                           'timestamp': self.timestamp,
                           'type': 'Cybereason',
                           'description': 'Cybereason reports'}
        return {'source': self.source, 'report': self.report}

    # Create vulnerability Object as per CAR data model from data source
    def handle_vulnerability(self, obj):
        """create vulnerability object"""
        if obj:
            for vuln in obj:
                if vuln["status"] != "Active":
                    continue
                res = {}
                res['name'] = vuln["displayName"]
                res['external_id'] = vuln["guid"]
                res["description"] = vuln["malopDetectionType"]
                res["disclosed_on"] = vuln["creationTime"]
                res["published_on"] = vuln["lastUpdateTime"]
                res["base_score"] = get_vulnerability_score(vuln["severity"])
                self.add_collection('vulnerability', res, 'external_id')
                # asset vulnerability edge creation
                if vuln.get('machines'):
                    for asset in vuln['machines']:
                        asset_id = asset['guid']
                        asset_vulnerability = {'_from_external_id': asset_id,
                                               '_to_external_id': vuln["guid"],
                                               }
                        self.add_edge('asset_vulnerability', asset_vulnerability)

    # Create asset Object as per CAR data model from data source
    def handle_asset(self, obj):
        """create asset object"""
        if obj:
            for asset in obj:
                res = {}
                res['external_id'] = asset['guid']
                res['name'] = asset['machineName']
                if asset.get('osVersionType'):
                    res['asset_type'] = asset['osVersionType']
                res['source'] = context().args.source
                self.add_collection('asset', res, 'external_id')

    def handle_hostname(self, obj):
        if obj:
            for asset in obj:
                res = {}
                res['host_name'] = asset['machineName']
                if asset.get('fqdn'):
                    res['_key'] = asset['fqdn']
                else:
                    res['_key'] = asset['machineName'].lower()
                self.add_collection('hostname', res, '_key')

                # asset_hostname edge
                self.add_edge('asset_hostname', {'_from_external_id': asset['guid'],
                                                 '_to': res['_key']})

    def handle_application(self, obj):
        if obj:
            for asset in obj:
                res = {}
                res['name'] = asset['osVersionType']
                res['is_os'] = True
                res['external_id'] = asset['sensorId']
                self.add_collection('application', res, 'external_id')
                # asset_application edge
                self.add_edge('asset_application', {'_from_external_id': asset['guid'],
                                                    '_to_external_id': res['external_id']})

    # Create ip address Object as per CAR data model from data source
    def handle_ipaddress(self, obj):
        """create ipaddress object"""
        for interface in obj:
            if interface.get("internalIpAddress"):
                res = {}
                res['name'] = "internalIpAddress:" + interface.get("internalIpAddress")
                res['_key'] = interface.get("internalIpAddress")
                self.add_collection('ipaddress', res, '_key')
                asset_ipaddress = {'_from_external_id': interface['guid'],
                                   '_to': res['_key']}
                self.add_edge('asset_ipaddress', asset_ipaddress)
            if interface.get("externalIpAddress"):
                res = {}
                res['name'] = "externalIpAddress:" + interface.get("externalIpAddress")
                res['_key'] = interface.get("externalIpAddress")
                self.add_collection('ipaddress', res, '_key')
                asset_ipaddress = {'_from_external_id': interface['guid'],
                                   '_to': res['_key']}
                self.add_edge('asset_ipaddress', asset_ipaddress)

    # Create mac address Object as per CAR data model from data source
    def handle_macaddress(self, obj):
        """create macaddress object"""
        for interface in obj:
            for ipaddress in [interface["internalIpAddress"], interface["externalIpAddress"]]:
                for key, value in interface["mac_list"].items():
                    if ipaddress == key:
                        for mac in value:
                            if mac != '':
                                res = {}
                                res['name'] = 'macaddress/' + mac
                                res['_key'] = mac
                                self.add_collection('macaddress', res, '_key')
                                # ipaddress_macaddress edge
                                ipaddress_mac = {'_from': "ipaddress/" + ipaddress,
                                                 '_to': "macaddress/" + mac}
                                self.add_edge('ipaddress_macaddress', ipaddress_mac)
