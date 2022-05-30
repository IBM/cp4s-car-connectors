import time
import datetime
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = {
        'asset': ['asset', 'users', 'account'],
        'application': ['application'],
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
    """returns: current time in milli sec"""
    return round(time.time() * 1000)


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry
            self.source = {'_key': context().args.source,
                           'name': "Okta",
                           'description': 'Identity and Access management service',
                           'product_link': "https://www.okta.com"}
            self.report = {'_key': str(self.timestamp),
                           'timestamp': self.timestamp,
                           'type': 'Okta',
                           'description': 'Okta reports'}
        return {'source': self.source, 'report': self.report}

    # Create asset Object as per CAR data model from data source
    def handle_asset(self, obj):
        """create asset object"""
        if obj:
            for asset in obj:
                res = {}
                res['external_id'] = asset['id']
                res['name'] = asset['profile'].get('firstName') + asset['profile'].get('lastName')
                res['description'] = asset['credentials']['provider']['type']
                res['asset_type'] = 'user'
                self.add_collection('asset', res, 'external_id')

    # Create user Object as per CAR data model from data source
    def handle_users(self, obj):
        """create asset object"""
        if obj:
            for asset in obj:
                res = {}
                res['external_id'] = asset['profile']['email']
                res['username'] = asset['profile'].get('login')
                res['user_category'] = asset['credentials']['provider']['type']
                res['email'] = asset['profile']['email']
                res['Last_password_change'] = asset['passwordChanged']
                res['Last_login'] = asset['lastLogin']
                if asset['profile'].get('firstName'):
                    res['Given_name'] = asset['profile']['firstName']
                if asset['profile'].get('lastName'):
                    res['Family_name'] = asset['profile']['lastName']
                res['Active'] = True if asset['status'] == 'ACTIVE' else False

                self.add_collection('user', res, 'external_id')

    def handle_account(self, obj):
        if obj:
            for asset in obj:
                res = {}
                res['name'] = asset['profile'].get('firstName') + asset['profile'].get('lastName')
                # user account in okta tenant
                res['external_id'] = asset['_links']['self']['href'].split('/')[2] + ":" + asset['id']
                self.add_collection('account', res, 'external_id')

                # asset_account edge
                self.add_edge('asset_account', {'_from_external_id': asset['id'],
                                                '_to_external_id': res['external_id']})

                # user_account edge
                self.add_edge('user_account', {'_from_external_id': asset['profile']['email'],
                                               '_to_external_id': res['external_id']})

    def handle_application(self, obj):
        if obj:
            for app in obj:
                res = {}
                res['name'] = app['name']
                res['external_id'] = app['id']
                res['Status'] = app['status']
                res['app_type'] = app['signOnMode']
                if app['_links'].get('appLinks'):
                    res['app_link'] = app['_links']['appLinks'][0]['href']
                res['policies'] = app['_links']['policies']['href']
                self.add_collection('application', res, 'external_id')

                # asset_application edge
                if app.get('users'):
                    for usr in app['users']:
                        self.add_edge('asset_application', {'_from_external_id': usr['id'],
                                                            '_to_external_id': res['external_id']})

    def handle_vulnerability(self, obj):
        if obj:
            for vulnerability in obj:
                res = dict()
                res['name'] = vulnerability['legacyEventType']
                res['external_id'] = vulnerability['legacyEventType']
                res['description'] = vulnerability['displayMessage'] + vulnerability['outcome']['result']
                res['published_on'] = vulnerability['published']
                res['base_score'] = 1
                self.add_collection('vulnerability', res, 'external_id')

                # asset_vulnerability edge
                if vulnerability.get('actor'):
                    self.add_edge('asset_vulnerability', {'_from_external_id': vulnerability['actor']['id'],
                                                          '_to_external_id': res['external_id'],
                                                          'client_ip': vulnerability['client']['ipAddress'],
                                                          'risk_score': vulnerability['score']})
