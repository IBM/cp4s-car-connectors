import time
import httpagentparser
from datetime import datetime, timezone
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = {
    'application': ['asset', 'application'],
    'user': ['user', 'account'],
    'client': ['asset', 'application', 'ipaddress', 'geolocation']
}


def get_report_time():
    """
    Convert current utc time to epoch time
    """
    delta = datetime.utcnow() - datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


def get_current_epoch_time():
    """returns: current time in milli sec"""
    return round(time.time() * 1000)


def get_epoch_time(time_obj):
    """
    Convert string format time to epoch time
    parameters:
            time_obj(str): date time in string format
    returns:
            epoch time
    """
    time_obj = datetime.strptime(time_obj, '%Y-%m-%dT%H:%M:%S.%fZ')
    delta = time_obj - datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


def format_datetime(value):
    """
    Converts milliseconds to timestamp
    :param: milliseconds(int)
    :return: str, converted timestamp
    """
    converted_time = (datetime.fromtimestamp(int(value) / 1000,
                                             timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
    return converted_time


def epoch_to_datetime_conv(epoch_time):
    """
    Convert epoch time to date format time
    :param epoch_time: time in epoch
    :return: date(utc format)
    """
    epoch_time = float(epoch_time) / 1000.0
    date_time = datetime.fromtimestamp(epoch_time).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return date_time


def get_asset_id(event):
    """
    Construct asset(client) external id from event information
    :param event: log event
    :return: external_id(string)
    """
    asset_external_id = None
    ipaddress = event['client']['ipAddress']
    if event.get('target'):
        for target in event['target']:
            if target['type'] == 'AppInstance':
                asset_external_id = target['id']
    external_id = f'ip_{ipaddress}'
    if asset_external_id:
        external_id = f'app_{asset_external_id}_ip_{ipaddress}'
    return external_id


def get_browser_version(user_agent):
    """
    return version of the browser
    :param : userAgent
    :return: browser version(string)
    """
    detections = httpagentparser.simple_detect(user_agent)
    # keep browser version like <browser>_Ver<version>
    browser_version = detections[1].replace(' ', '_Ver')
    return browser_version


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry
            self.source = {'_key': context().args.source,
                           'name': "Okta",
                           'description': 'Identity and Access Management service',
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
            # user login client as asset
            if obj[0].get('client'):
                for asset in obj:
                    res = {}
                    user_id = asset['actor']['id']
                    # handling users assigned to an application
                    # this case asset, account nodes are present,
                    # we are adding asset_account edge.
                    if asset['eventType'] == 'application.user_membership.add':
                        for record in asset['target']:
                            if record['type'] == 'AppInstance':
                                res['external_id'] = record['id']
                            if record['type'] == 'User':
                                user_id = record['id']
                    else:
                        browser = asset['client']['userAgent']['browser']
                        os = asset['client']['userAgent']['os']
                        ipaddress = asset['client']['ipAddress']
                        device = asset['client']['device']
                        res['name'] = f'{browser} on {os} {device} from {ipaddress}'
                        res['external_id'] = get_asset_id(asset)
                        self.add_collection('asset', res, 'external_id')
                        # asset_account edge
                    self.add_edge('asset_account', {'_from_external_id': res['external_id'],
                                                    '_to_external_id': user_id})
            else:
                # Application as asset
                for asset in obj:
                    res = {}
                    res['external_id'] = asset['id']
                    res['name'] = asset['label']
                    self.add_collection('asset', res, 'external_id')

                    # Handle asset_account
                    for user in asset.get('users'):
                        self.add_edge('asset_account', {'_from_external_id': res['external_id'],
                                                        '_to_external_id': user['id']})

    # Create user Object as per CAR data model from data source
    def handle_user(self, obj):
        """create user object"""
        if obj:
            for asset in obj:
                res = {}
                res['external_id'] = asset['profile']['email']
                res['email'] = asset['profile']['email']
                res['username'] = asset['profile'].get('login')
                res['user_category'] = asset['credentials']['provider']['type']
                res['email'] = asset['profile']['email']
                res['last_password_change'] = asset['passwordChanged']
                res['last_login'] = asset['lastLogin']
                if asset['profile'].get('firstName'):
                    res['given_name'] = asset['profile']['firstName']
                if asset['profile'].get('lastName'):
                    res['family_name'] = asset['profile']['lastName']
                res['active'] = bool(asset['status'] == 'ACTIVE')

                self.add_collection('user', res, 'external_id')

    # Create Account Object as per CAR data model from data source
    def handle_account(self, obj):
        """create account object"""
        if obj:
            for usr in obj:
                res = {}
                res['name'] = usr['profile'].get('firstName') + usr['profile'].get('lastName')
                # user account in okta tenant
                res['external_id'] = usr['id']
                self.add_collection('account', res, 'external_id')
                # user_account edge
                self.add_edge('user_account', {'_from_external_id': usr['profile']['login'],
                                               '_to_external_id': res['external_id']})

    # Create Application Object as per CAR data model from data source
    def handle_application(self, obj):
        """create user object"""
        if obj:
            # user log-in client
            if obj[0].get('client'):
                for app in [event for event in obj if event['eventType'] != 'application.user_membership.add']:
                    # OS as application
                    os_res = {}
                    os_res['name'] = app['client']['userAgent']['os']
                    os_res['external_id'] = app['client']['userAgent']['os']
                    os_res['app_type'] = 'os'
                    os_res['is_os'] = True
                    self.add_collection('application', os_res, 'external_id')
                    # Browser as application
                    app_res = {}
                    app_res['name'] = app['client']['userAgent']['browser']
                    user_agent = app['client']['userAgent']['rawUserAgent']
                    app_res['external_id'] = get_browser_version(user_agent)
                    app_res['app_type'] = 'browser'
                    app_res['is_os'] = False
                    self.add_collection('application', app_res, 'external_id')
                    asset_external_id = get_asset_id(app)
                    for external_id in [os_res['external_id'], app_res['external_id']]:
                        self.add_edge('asset_application', {'_from_external_id': asset_external_id,
                                                            '_to_external_id': external_id})
            else:
                # login application
                for app in obj:
                    res = {}
                    res['name'] = app['label']
                    res['external_id'] = app['name'] + '_' + app['id']
                    res['status'] = app['status']
                    res['app_type'] = app['signOnMode']
                    app["is_os"] = False
                    if app['_links'].get('appLinks'):
                        res['app_link'] = app['_links']['appLinks'][0]['href']
                    res['policies'] = app['_links']['policies']['href']
                    self.add_collection('application', res, 'external_id')
                    self.add_edge('asset_application', {'_from_external_id': app['id'],
                                                        '_to_external_id': res['external_id']})

    # Create ip address Object as per CAR data model from data source
    def handle_ipaddress(self, obj):
        """create ipaddress object"""
        for interface in obj:
            res = {}
            res['_key'] = interface["client"]['ipAddress']
            self.add_collection('ipaddress', res, '_key')

            # asset_ipaddress edge
            asset_external_id = get_asset_id(interface)
            self.add_edge('asset_ipaddress', {'_from_external_id': asset_external_id,
                                              '_to_external_id': res['_key']})

    # Create geolocation Object as per CAR data model from data source
    def handle_geolocation(self, obj):
        """create geolocation object"""
        for loc in obj:
            res = {}
            res['latitude'] = loc["client"]['geographicalContext']['geolocation']['lat']
            res['longitude'] = loc["client"]['geographicalContext']['geolocation']['lon']
            res['external_id'] = f'{res["latitude"]},{res["longitude"]}'
            self.add_collection('geolocation', res, 'external_id')
            # asset_geolocation edge
            asset_external_id = get_asset_id(loc)
            self.add_edge('asset_geolocation', {'_from_external_id': asset_external_id,
                                                '_to_external_id': res['external_id']})
