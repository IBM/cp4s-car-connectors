import requests, base64, datetime, json
from car_framework.context import context


class AssetServer(object):

    def __init__(self):
        # Api authentication  to call data-source  API
        auth = base64.encodestring(('%s:%s' % (context().args.username, context().args.password)).encode()).decode().strip()
        self.server_headers = {'Accept' : 'application/json', 'Authorization': 'Basic ' + auth}
        self.cache = {}

    # Get entity for the specific id cached
    def get_object(self, url):
        cached = self.cache.get(url)
        if cached: return cached
        resp = requests.get(url, headers=self.server_headers)
        if resp.status_code != 200:
            if resp.status_code == 404:
                return None
            else:
                raise Exception('Error when getting resource at %s: %s' % (url, resp.status_code))
        res = resp.json()
        self.cache[url] = res
        return res

    # Get list of entities as per the identifiers passed.
    def get_objects(self, asset_server_endpoint, ids):
        resp = requests.get('%s/%s/?pk=%s' % (context().args.server, asset_server_endpoint, ','.join([str(id) for id in ids])), headers=self.server_headers)
        if resp.status_code != 200:
            raise Exception('Error when getting resources: %s' % (resp.status_code))
        json_data = resp.json() 
        for obj in json_data:
            self._cache(asset_server_endpoint, obj)
        return json_data

    # Pulls asset data for all collection entities
    def get_collection(self, asset_server_endpoint):
        resp = requests.get('%s/%s' % (context().args.server, asset_server_endpoint), headers=self.server_headers)
        if resp.status_code != 200:
            raise Exception('Error when getting resources: %s' % (resp.status_code))
        json_data = resp.json() 
        for obj in json_data:
            self._cache(asset_server_endpoint, obj)
        return json_data

    # Cache object entity for later use 
    def _cache(self, endpoint, obj):
        id = obj.get('pk')
        if id:
            self.cache['%s/%s/%s/' % (context().args.server, endpoint, id)] = obj

    # To get the save point in data source. If data source doesn't have it then this function can be deleted.
    def get_model_state_id(self):
        resp = requests.get('%s/model_state_id' % context().args.server, headers=self.server_headers)
        if resp.status_code != 200:
            return None
        json_data = resp.json()
        return json_data.get('model_state_id')

    # This function has logic to gather all information required to pull data between two save points
    def get_model_state_delta(self, last_model_state_id, new_model_state_id):
        resp = requests.get('%s/delta' % context().args.server, params={'from':last_model_state_id, 'to': new_model_state_id}, headers=self.server_headers)
        if resp.status_code != 200:
            raise Exception('Error when trying to retrieve asset model delta: %d' % resp.status_code)
        delta = resp.json()
        return delta.get('delta', {})

