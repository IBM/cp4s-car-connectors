from car_framework.context import context
from car_framework.data_handler import BaseDataHandler
from datetime import datetime
import dateutil.parser as dparser

ACTIVE = True
BASE_SCORE_MAP = {"high": 8, "medium": 5, "low": 2, "informational": 0}


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry and it is compuslory for each imports API call
            self.source = {'_key': context().args.source, 'name': context().args.tenantID, 'description': 'Microsoft Defender for Endpoint imports', 'product_link' : 'https://securitycenter.windows.com/'}
            self.report = {'_key': str(self.timestamp), 'timestamp' : self.timestamp, 'type': 'Microsoft Defender for Endpoint', 'description': 'Microsoft Defender for Endpoint imports'}

        return {'source': self.source, 'report': self.report}

    def handle_asset(self, obj):
        asset = dict()
        if obj:
            asset['external_id'] = obj['id']
            asset['name'] = obj['computerDnsName']

            self.add_collection('asset', asset, 'external_id')

    def handle_ipaddress(self, obj):
        if obj.get('IPAddress'):
            for ips in obj['IPAddress']:
                ipaddress = dict()
                ipaddress['_key'] = ips
                self.add_collection('ipaddress', ipaddress, '_key')

    def handle_macaddress(self, obj):
        if obj.get('MacAddress'):
            macaddress = dict()
            macaddress['_key'] = obj['MacAddress']
            self.add_collection('macaddress', macaddress, '_key')

    def handle_hostname(self, obj):
        if obj.get("computerDnsName"):
            hostname = dict()
            hostname['_key'] = obj["computerDnsName"]
            hostname['description'] = "hostname of the machine"
            self.add_collection('hostname', hostname, '_key')

    def handle_ipaddress_macaddress(self, obj):
        if obj.get('MacAddress') and obj.get("lastIpAddress"):
            for ips in obj["lastIpAddress"]:
                ipaddress_macaddress = dict()
                ipaddress_macaddress['_from'] = 'ipaddress/' + str(ips)
                ipaddress_macaddress['_to'] = 'macaddress/' + str((obj['MacAddress']))
                self.add_edge('ipaddress_macaddress', ipaddress_macaddress)

    def handle_asset_ipaddress(self, obj):
        if obj.get('IPAddress') and obj.get('id'):
            for ips in obj['IPAddress']:
                asset_ipaddress = dict()
                asset_ipaddress['_from_external_id'] = obj["id"]
                asset_ipaddress['_to'] = 'ipaddress/' + ips
                self.add_edge('asset_ipaddress', asset_ipaddress)

    def handle_asset_macaddress(self, obj):
        if obj.get('MacAddress') and obj.get('id'):
            asset_macaddress = dict()
            asset_macaddress['_from_external_id'] = obj['id']
            asset_macaddress['_to'] = 'macaddress/' + str(obj['MacAddress'])
            self.add_edge('asset_macaddress', asset_macaddress)

    def handle_asset_hostname(self, obj):
        if obj and obj.get('id') and obj.get('computerDnsName'):
            asset_hostname = dict()
            asset_hostname['_from_external_id'] = obj['id']
            asset_hostname['_to'] = 'hostname/' + str(obj["computerDnsName"])
            self.add_edge('asset_hostname', asset_hostname)

    def handle_user(self, obj):
        user = dict()
        if obj.get('accountName'):
            user['external_id'] = obj['accountName']
            self.add_collection('user', user, 'external_id')

    def handle_account(self, obj):
        account = dict()
        if obj.get('accountName'):
            account['external_id'] = obj['accountName']
            account['name'] = obj['accountName']
            self.add_collection('account', account, 'external_id')

    def handle_user_account(self, obj):
        user_account = dict()
        if obj.get('accountName'):
            user_account['_from_external_id'] = obj['accountName']
            user_account['_to_external_id'] = obj['accountName']
            self.add_edge('user_account', user_account)

    def handle_asset_account(self, obj):
        asset_account = dict()
        if obj and obj.get("DeviceId") and obj.get('accountName'):
            asset_account['_from_external_id'] = obj["DeviceId"]
            asset_account['_to_external_id'] = obj['accountName']
            self.add_edge('asset_account', asset_account)

    def handle_account_hostname(self, obj):
        account_hostname = dict()
        if obj and obj.get("DeviceId") and obj.get('accountName'):
            account_hostname['_to'] = 'hostname/' + str(obj["DeviceId"])
            account_hostname['_from_external_id'] = obj["accountName"]
            self.add_edge('account_hostname', account_hostname)

    def handle_vulnerability(self, obj):
        vulnerability = dict()
        if obj and 'CveId' in obj and obj['CveId']:
            if obj['CveId'] and obj['CvssScore']:
                vulnerability['external_id'] = obj['CveId']
                vulnerability['name'] = obj['CveId']
                vulnerability['description'] = obj['VulnerabilityDescription']
                vulnerability['published_on'] = dparser.parse(obj['PublishedDate']).timestamp()
                vulnerability['base_score'] = round(obj['CvssScore'])
                self.add_collection('vulnerability', vulnerability, 'external_id')

        elif obj and 'alertCreationTime' in obj:
            vulnerability['external_id'] = obj['id']
            vulnerability['name'] = obj['title']
            vulnerability['description'] = obj['description']
            vulnerability['disclosed_on'] = dparser.parse(obj['firstEventTime']).timestamp()
            vulnerability['published_on'] = dparser.parse(obj['alertCreationTime']).timestamp()
            vulnerability['base_score'] = BASE_SCORE_MAP.get(obj['severity'].lower(), 0)
            self.add_collection('vulnerability', vulnerability, 'external_id')

    def handle_asset_vulnerability(self, obj):
        asset_vulnerability = dict()
        if obj and 'CveId' in obj:
            asset_vulnerability['_from_external_id'] = obj['DeviceId']
            asset_vulnerability['_to_external_id'] = obj['CveId']
            self.add_edge('asset_vulnerability', asset_vulnerability)
        elif obj and 'alertCreationTime' in obj:
            asset_vulnerability['_from_external_id'] = obj['machineId']
            asset_vulnerability['_to_external_id'] = obj['id']
            self.add_edge('asset_vulnerability', asset_vulnerability)

    def handle_application(self, obj):
        application = dict()
        if all(k in obj for k in ('SoftwareVersion', 'DeviceId', 'SoftwareName', 'SoftwareVendor')):
            app_name = obj['SoftwareVendor'] + ':' + obj['SoftwareName'] + ':' + obj[
                'SoftwareVersion']
            application['name'] = app_name
            application['external_id'] = app_name
        elif 'healthStatus' in obj and 'osPlatform' in obj:
            application['name'] = obj['osPlatform']
            application['is_os'] = ACTIVE
            application['external_id'] = obj['osPlatform']

        if application:
            self.add_collection('application', application, 'external_id')

    def handle_asset_application(self, obj):
        asset_application = dict()
        if all(k in obj for k in ('SoftwareVersion', 'DeviceId', 'SoftwareName', 'SoftwareVendor')):
            asset_application['_from_external_id'] = obj['DeviceId']
            asset_application['_to_external_id'] = obj['SoftwareVendor'] + ':' + obj['SoftwareName'] + ':' + \
                obj['SoftwareVersion']
        elif 'healthStatus' in obj and 'osPlatform' in obj:
            asset_application['_from_external_id'] = obj['id']
            asset_application['_to_external_id'] = obj['osPlatform']

        if asset_application:
            self.add_edge('asset_application', asset_application)

    def handle_application_vulnerability(self, obj):
        application_vulnerability = dict()
        if all(k in obj for k in ('CvssScore', 'SoftwareVersion', 'DeviceId', 'SoftwareName', 'SoftwareVendor')):
            application_vulnerability['_from_external_id'] = obj['SoftwareVendor'] + ':' + obj['SoftwareName'] + ':' + \
                obj['SoftwareVersion']
            application_vulnerability['_to_external_id'] = obj['CveId']
            self.add_edge('application_vulnerability', application_vulnerability)
