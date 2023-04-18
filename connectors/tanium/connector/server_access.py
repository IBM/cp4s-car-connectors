import json
import requests

from car_framework.context import context
from car_framework.util import DatasourceFailure, ErrorCode
from car_framework.server_access import BaseAssetServer
from connector.error_response import ErrorResponder



class AssetServer(BaseAssetServer):
    def __init__(self):
        # Api authentication to call data-source  API

        self.server = "https://" + context().args.host + ":" + str(context().args.port)
        self.graphql_endpoint = self.server + "/plugin/products/gateway/graphql"
        self.headers = {
            "session": context().args.access_token,
            "Content-Type": "application/json"
        }
        self.session = requests.session()

    def test_connection(self):
        try:
            query = """
                query {
                    endpoints{
                        totalRecords
                    }
                }
            """
            response = self.execute_query(query)
            response_json = json.loads(response.text)
            if response.status_code == 200:
                print("good")
                print(response_json)
                code = 0
            else:
                code = 1
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    def query_tanium_endpoints(self, variables=None):
        """
        Execute endpoints query
        parameters:
            variables(dict): graphql query variables
        returns:
            json_data(dict): Api response
        """
        if variables is None:
            variables = {}
        query = """
            query {
                endpoints{
                    edges {
                        node {
                          id,
                          name,
                          manufacturer,
                          eidFirstSeen,
                          eidLastSeen,
                          services {
                            name,
                            displayName,
                            status
                          },
                          installedApplications {
                            name,
                            version
                          },
                          deployedSoftwarePackages {
                            id,
                            vendor,
                            version
                          },
                          ipAddress,
                          ipAddresses,
                          domainName,
                          macAddresses,
                          primaryUser{
                            name,
                            email,
                            department
                          },
                          os {
                            name
                          },
                        discover {
                          openPorts
                        }
                        risk {
                          totalScore
                        }
                      }
                    }
                }
            }
        """
        try:
            api_response = self.execute_query(query, variables)
            # api_response_status_code = json.loads(api_response.status_code)
            api_response_json = json.loads(api_response.text)
        except Exception as ex:
            return_obj = {}
            ErrorResponder.fill_error(return_obj, ex)
            raise Exception(return_obj)
        return api_response_json

    def execute_query(self, query, variables=None):
        """
        Execute query from datasource using graphql api
        parameters:
            query(str): graphql query in plain string
        returns:
            json_data(dict): Api response
        """
        if variables is None:
            variables = {}
        try:

            api_response = requests.post(self.graphql_endpoint, json={'query': query, 'variables': variables},
                                         headers=self.headers, verify=False)

        except Exception as ex:
            return_obj = {}
            ErrorResponder.fill_error(return_obj, ex)
            raise Exception(return_obj)
        return api_response
