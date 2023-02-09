import json
import requests, base64

from car_framework.context import context
from car_framework.util import DatasourceFailure, ErrorCode
from car_framework.server_access import BaseAssetServer

import randori_api
from randori_api.api import default_api
from base64 import b64encode


class AssetServer(BaseAssetServer):
    def __init__(self):
        # Api authentication to call data-source  API
        self.configuration = randori_api.Configuration(
            access_token=context().args.access_token,
            host= 'https://{}'.format(context().args.host)
        )

    def test_connection(self):
        with randori_api.ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            api_instance = default_api.DefaultApi(api_client)
            query = {
                "condition": "OR",
                "rules": [{
                     "field": "table.affiliation_state",
                     "id": "table.affiliation_state",
                     "input": "text",
                     "operator": "equal",
                     "type": "object",
                     "ui_id": "show_unaffiliated",
                     "value": "Unaffiliated"
                }]
            }

            # We need the query to be a string in order to base64 encode it easily
            query = json.dumps(query)

            # Randori expects the 'q' query to be base64 encoded in string format
            query = b64encode(query.encode()).decode()
            try:
                api_response = api_instance.get_hostname(offset=1, limit=1, sort=["last_seen"], q=query, reversed_nulls=True)
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
        # Enter a context with an instance of the API client
        with randori_api.ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            api_instance = default_api.DefaultApi(api_client)
            try:
                api_response = api_instance.get_all_detections_for_target(offset=offset, limit=limit, sort=sort, q=q,
                                                                          reversed_nulls=reversed_nulls)
                return api_response
            except randori_api.exceptions.UnauthorizedException as e:
                raise DatasourceFailure(e, ErrorCode.DATASOURCE_FAILURE_AUTH.value)
            except randori_api.ApiException as e:
                raise e
