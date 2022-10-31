import json
import requests, base64

from car_framework.context import context
from car_framework.util import DatasourceFailure
from car_framework.server_access import BaseAssetServer

import randori_api
from randori_api.api import default_api


class AssetServer(BaseAssetServer):
    def __init__(self):
        # Api authentication to call data-source  API
        with open('connector/randori_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        auth = context().args.access_token
        self.server_headers = {'Accept': 'application/json', 'Authorization': auth}
        self.server = "https://" + context().args.server
        self.cache = {}

    def test_connection(self):
        try:
            self.get_collection('recon/api/v1/hostname')
            code = 0
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    # Get entity for the specific id cached
    def get_object(self, asset_server_endpoint, resource):
        try:
            cache_key = f"{context().args.server}/{asset_server_endpoint}/{resource}"
            cache_value = self.cache.get(cache_key)
            if cache_value:
                return cache_value

            resp = requests.get('%s/%s/%s' % (context().args.server, asset_server_endpoint, resource),
                                headers=self.server_headers)
            if resp.status_code != 200:
                if resp.status_code == 404:
                    return None
                else:
                    raise DatasourceFailure('Error when getting resource at %s/%s: %s' % (
                        asset_server_endpoint, resource, resp.status_code))
            res = resp.json()
            self.cache[cache_key] = res
            return res
        except Exception as e:
            raise e

    # Pulls asset data for all collection entities
    def get_collection(self, asset_server_endpoint):
        try:
            resp = requests.get(f"{context().args.server}/{asset_server_endpoint}", headers=self.server_headers)
            if resp.status_code != 200:
                raise DatasourceFailure('Error when getting resources: %s' % (resp.status_code))
            json_data = resp.json()
            for obj in json_data['data']:
                self._cache(asset_server_endpoint, obj)
            return json_data
        except Exception as e:
            raise e

    # Cache object entity for later use
    def _cache(self, endpoint, obj):
        id = obj.get('id')
        if id:
            self.cache['%s/%s/%s' % (context().args.server, endpoint, id)] = obj

    # GET /recon/api/v1/entity/{entity_id}/comment
    def get_comment(self, entity_id):
        try:
            cache_key = '%s/recon/api/v1/entity/%s/comment' % (context().args.server, entity_id)
            cache_value = self.cache.get(cache_key)
            if cache_value:
                return cache_value
            resp = requests.get('%s/recon/api/v1/entity/%s/comment' % (context().args.server, entity_id),
                                headers=self.server_headers)
            if resp.status_code != 200:
                raise DatasourceFailure('Error when getting resources: %s' % resp.status_code)
            json_data = resp.json()
            self.cache[cache_key] = json_data
            return json_data
        except Exception as e:
            raise e

    def get_detections_for_target(self, offset, limit, sort, q, reversed_nulls):
        """
        Fetch data /recon/api/v1/all-detections-for-target
        parameters:
            offset	int	offset into avilable records after filtering	[optional]
            limit	int	maximum number of records to return	[optional]
            sort	[str]	fields in the object to sort by, in order of precedence, minus indicates descending	[optional]
            q	    str	base64 encoded jquery querybuilder complex search field	[optional]
            reversed_nulls	bool	if true, sorts nulls as if smaller than any nonnull value for all sort parameters.
                                    otherwise (default) treats as if larger	[optional]
        returns:
            AllDetectionsForTargetGetOutput,
            see https://github.com/RandoriDev/randori-api-sdk/blob/master/docs/AllDetectionsForTargetGetOutput.md
        """

        configuration = randori_api.Configuration(
            host=self.server,
            # TODO long lived token
            access_token=context().args.access_token
        )

        # Enter a context with an instance of the API client
        with randori_api.ApiClient(configuration) as api_client:
            # Create an instance of the API class
            api_instance = default_api.DefaultApi(api_client)
            try:
                api_response = api_instance.get_all_detections_for_target(offset=offset, limit=limit, sort=sort, q=q,
                                                                          reversed_nulls=reversed_nulls)
                return api_response
            except randori_api.ApiException as e:
                raise e
