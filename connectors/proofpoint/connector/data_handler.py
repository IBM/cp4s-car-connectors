import datetime
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

# maps asset-server endpoints to CAR service endpoints
endpoint_mapping = \
    {'siem': ['assets', 'vulnerabilities'],
     'people': ['accounts', 'users']}


def get_report_time():
    """
    Convert current utc time to epoch time
    """
    delta = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


def get_epoch_time(time_obj):
    """
    Convert string format time to epoch time
    parameters:
            time_obj(str): date time in string format
    returns:
            epoch time
    """
    time_obj = datetime.datetime.strptime(time_obj, '%Y-%m-%dT%H:%M:%S.%fZ')
    delta = time_obj - datetime.datetime(1970, 1, 1)
    milliseconds = delta.total_seconds() * 1000
    return milliseconds


def get_base_score(obj, classification):
    """
    Get base score of threat based on category
    parameters:
            obj(dict): api response
            classification(str): Threat classification
    returns:
            threat score
    """
    threat_score = classification.lower() + 'Score'
    base_score = obj.get(threat_score)
    # CAR service supports score range from 0-10.
    # ProofPoint threats has score from 0-100
    # So converting score from range 0-100 to 0-10
    base_score = int(base_score) / 10
    return base_score


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry
            self.source = {'_key': context().args.source,
                           'name': "Proofpoint Threat Attack Protection",
                           'description': 'Proofpoint Targeted Attack Protection (TAP) helps detect,\
                                mitigate and block advanced threats that target people through email',
                           'product_link': "https://threatinsight.proofpoint.com"}
            self.report = {'_key': str(self.timestamp),
                           'timestamp': self.timestamp,
                           'type': 'Proofpoint Targeted Attack Protection',
                           'description': 'Proofpoint Targeted Attack Protection reports'}
        return {'source': self.source, 'report': self.report}

    # Copies the source object to CAR data model object if attribute have same name
    def copy_fields(self, obj, *fields):
        res = {}
        for field in fields:
            res[field] = obj[field]
        return res

    # Handlers
    # Each endpoint defined in the above endpoint_mapping object should have a handle_* method

    # Create vulnerability Object as per CAR data model from data source
    def handle_vulnerabilities(self, obj):
        for threat in obj['threatsInfoMap']:
            if threat['threatStatus'] != "active":
                continue
            res = self.copy_fields(obj, )
            res['name'] = threat['classification'] + ':' + threat['threat']
            res['base_score'] = get_base_score(obj, threat['classification'])
            res['description'] = threat['classification'] + ' ' + threat['threatType']
            res['disclosed_on'] = get_epoch_time(threat['threatTime'])
            res['source'] = context().args.source
            res['external_id'] = threat['threatID']
            self.add_collection('vulnerability', res, 'external_id')

    # Create asset Object as per CAR data model from data source
    def handle_assets(self, obj):
        for recipient in obj['recipient']:
            res = self.copy_fields(obj, )
            res['name'] = recipient.split('@')[0]
            res['external_id'] = recipient
            res['description'] = "ProofPoint user of " + recipient.split('@')[1]
            res['asset_type'] = 'user'
            res['source'] = context().args.source
            flag = False # Active threats only has active assets

            for vulnerability in obj.get('threatsInfoMap'):
                if vulnerability['threatStatus'] != "active":
                    continue
                self.add_edge('asset_vulnerability',
                              {'_from_external_id': res['external_id'],
                               '_to_external_id': vulnerability['threatID'],
                               'active': 'true',
                               'created': self.timestamp,
                               'report': self.timestamp,
                               'risk_score': get_base_score(obj, vulnerability['classification']),
                               'source': context().args.source})
                flag = True
            if flag:
                self.add_collection('asset', res, 'external_id')

    # Create account Object as per CAR data model from data source
    def handle_accounts(self, obj):
        res = self.copy_fields(obj, )
        if obj['identity']['name']:
            res['name'] = obj['identity']['name']
        else:
            res['name'] = (obj['identity']['emails'][0]).split('@')[0]
        res['external_id'] = obj['identity']['guid']
        res['active'] = 'true'
        res['cumulative_score'] = obj['threatStatistics']['attackIndex']
        res['source'] = context().args.source

        objects = self.collections.get('asset', [])
        for row in objects:
            if row['external_id'] == obj['identity']['emails'][0]:
                self.add_edge('asset_account',
                              {'_from_external_id': row['external_id'],
                               '_to_external_id': res['external_id'],
                               'active': 'true',
                               'created': self.timestamp,
                               'report': self.timestamp,
                               'source': context().args.source})
        self.add_collection('account', res, 'external_id')

    # Create user Object as per CAR data model from data source
    def handle_users(self, obj):
        res = self.copy_fields(obj, )
        if obj['identity']['name']:
            res['username'] = obj['identity']['name']
        else:
            res['username'] = (obj['identity']['emails'][0]).split('@')[0]
        res['external_id'] = obj['identity']['emails'][0]
        res['job_title'] = obj['identity']['title']
        res['email'] = obj['identity']['emails'][0]
        res['user_category'] = obj['identity']['vip']
        res['employee_id'] = obj['identity']['customerUserId']
        res['department'] = obj['identity']['department']
        res['active'] = 'true'
        res['cumulative_score'] = obj['threatStatistics']['attackIndex']
        res['source'] = context().args.source
        self.add_edge('user_account',
                      {'_from_external_id': res['external_id'],
                       '_to_external_id': obj['identity']['guid'],
                       'created': self.timestamp,
                       'report': self.timestamp,
                       'active': 'true'})
        self.add_collection('user', res, 'external_id')
