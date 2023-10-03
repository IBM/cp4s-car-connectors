import requests, base64

from car_framework.context import context
from car_framework.util import DatasourceFailure
from car_framework.server_access import BaseAssetServer


class AssetServer(BaseAssetServer):

    def __init__(self):
        # Api authentication  to call data-source  API
        auth = base64.encodebytes(('%s:%s' % (context().args.CONFIGURATION_AUTH_USERNAME, context().args.CONFIGURATION_AUTH_PASSWORD)).encode('utf8')).decode('utf8').strip()
        self.server_headers = {'Accept' : 'application/json', 'Authorization': 'Basic ' + auth}
        self.cache = {}

    def test_connection(self):
        try:
            self.get_collection('xrefproperties')
            code = 0
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    # Get entity for the specific id cached
    def get_object(self, url):
        try: 
            cached = self.cache.get(url)
            if cached: return cached
            resp = requests.get(url, headers=self.server_headers)
            if resp.status_code != 200:
                if resp.status_code == 404:
                    return None
                else:
                    raise DatasourceFailure('Error when getting resource at %s: %s' % (url, resp.status_code))
            res = resp.json()
            self.cache[url] = res
            return res
        except BaseException as e:
            raise DatasourceFailure(e.args[0])

    # Get list of entities as per the identifiers passed.
    def get_objects(self, asset_server_endpoint, ids):
        try:
            resp = requests.get('%s/%s/?pk=%s' % (context().args.CONFIGURATION_AUTH_URL, asset_server_endpoint, ','.join([str(id) for id in ids])), headers=self.server_headers)
            if resp.status_code != 200:
                raise DatasourceFailure('Error when getting resources: %s' % (resp.status_code))
            json_data = resp.json() 
            for obj in json_data:
                self._cache(asset_server_endpoint, obj)
            return json_data
        except Exception as e:
            raise DatasourceFailure(e.args[0])

    # Pulls asset data for all collection entities
    def get_collection(self, asset_server_endpoint):
        try: 
            resp = requests.get('%s/%s' % (context().args.CONFIGURATION_AUTH_URL, asset_server_endpoint), headers=self.server_headers)
            if resp.status_code != 200:
                raise DatasourceFailure('Error when getting resources: %s' % (resp.status_code))
            json_data = resp.json() 
            for obj in json_data:
                self._cache(asset_server_endpoint, obj)
            return json_data
        except Exception as e:
            raise DatasourceFailure(e.args[0])

    # Cache object entity for later use 
    def _cache(self, endpoint, obj):
        id = obj.get('pk')
        if id:
            self.cache['%s/%s/%s/' % (context().args.CONFIGURATION_AUTH_URL, endpoint, id)] = obj

    # To get the save point in data source. If data source doesn't have it then this function can be deleted.
    def get_model_state_id(self):
        try:
            resp = requests.get('%s/model_state_id' % context().args.CONFIGURATION_AUTH_URL, headers=self.server_headers)
            if resp.status_code != 200:
                return None
            json_data = resp.json()
            return json_data.get('model_state_id')
        except Exception as e:
            raise DatasourceFailure(e.args[0])

    # This function has logic to gather all information required to pull data between two save points
    def get_model_state_delta(self, last_model_state_id, new_model_state_id):
        try: 
            resp = requests.get('%s/delta' % context().args.CONFIGURATION_AUTH_URL, params={'from':last_model_state_id, 'to': new_model_state_id}, headers=self.server_headers)
            if resp.status_code != 200:
                raise DatasourceFailure('Error when trying to retrieve asset model delta: %d' % resp.status_code)
            delta = resp.json()
            return delta.get('delta', {})
        except Exception as e:
            raise DatasourceFailure(e.args[0])

