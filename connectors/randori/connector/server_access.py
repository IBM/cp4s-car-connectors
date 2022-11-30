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
        auth = context().args.access_token
        self.server_headers = {'Accept': 'application/json', 'Authorization': auth}
        self.cache = {}

    def test_connection(self):

        configuration = randori_api.Configuration(
            access_token=context().args.access_token
        )
        with randori_api.ApiClient(configuration) as api_client:
            # Create an instance of the API class
            api_instance = default_api.DefaultApi(api_client)
            sort = [
                "-affiliation_state",
            ]
            q = "q_example"
            try:
                api_response = api_instance.get_hostname(offset=1, limit=1, sort=sort, q=q, reversed_nulls=True)
                code = 0
            except randori_api.ApiException as e:
                context().logger.error('Error testing connection: %s' % e)
                code = 1
        return code

    def get_detections_for_target(self, offset, limit, sort, q, reversed_nulls):
        """
        Fetch data /recon/api/v1/all-detections-for-target
        parameters:
            offset	int	offset into available records after filtering [optional]
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
