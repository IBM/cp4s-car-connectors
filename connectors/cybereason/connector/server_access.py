import json
import requests
from car_framework.context import context
from car_framework.util import DatasourceFailure
from connector.data_handler import get_current_epoch_time
from connector.error_response import ErrorResponder


class AssetServer:

    def __init__(self):

        # Get server connection arguments from config file
        with open('connector/cybereason_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        # Data source url
        self.server = "https://" + context().args.host + ":" + context().args.port
        asset_server_endpoint = self.server + self.config['endpoint']['auth']
        data = {
            "username": context().args.username,
            "password": context().args.password
        }
        self.session = requests.session()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.get_collection("POST", asset_server_endpoint, data=data, headers=headers)

    def test_connection(self):
        try:
            asset_server_endpoint = self.server + self.config['endpoint']['auth']
            data = {
                "username": context().args.username,
                "password": context().args.password
            }
            self.session = requests.session()
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = self.get_collection('POST', asset_server_endpoint, data=data, headers=headers)
            if response.status_code == 200 and 'error' not in response.url:
                code = 0
            else:
                code = 1
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    # Pulls asset data for all collection entities
    def get_collection(self, method, asset_server_endpoint, data=None, headers=None):
        """
        Fetch data from datasource using api
        parameters:
            method(str): REST methode(GET, POST)
            asset_server_endpoint(str): api end point
            data(str): api input
        returns:
            json_data(dict): Api response
        """
        try:
            api_response = self.session.request(method, asset_server_endpoint,
                                                data=data, headers=headers)
        except Exception as ex:
            return_obj = {}
            ErrorResponder.fill_error(return_obj, ex)
            raise Exception(return_obj)

        return api_response

    def get_assets(self, last_model_state_id=None, incremental_delete=None):
        """
        Fetch the entire asset records from data source.
        parameters:
            last_model_state_id(datetime): last run time
        returns:
            results(list): Api response
        """
        assets = []
        headers = self.config['parameter']['headers']
        asset_server_endpoint = self.server + self.config['endpoint']['asset']
        if last_model_state_id:
            filter_query = [{
                "fieldName": "lastPylumUpdateTimestampMs",
                "operator": "GreaterOrEqualsTo",
                "values": [last_model_state_id]
            }]
        elif incremental_delete:
            filter_query = [
                {
                    "fieldName": "status",
                    "operator": "Equals",
                    "values": [
                        "Stale",
                        "Archived"
                    ]
                }
            ]
        else:
            filter_query = [
                {
                    "fieldName": "status",
                    "operator": "Equals",
                    "values": [
                        "Online",
                        "Offline"
                    ]
                }
            ]
        offset = 0
        has_more_results = True
        while has_more_results:
            query = json.dumps({
                "limit": 1000,
                "offset": offset,
                "filters": filter_query
            })
            response = self.get_collection("POST", asset_server_endpoint, data=query, headers=headers)
            if response.status_code != 200:
                return_obj = {}
                status_code = response.status_code
                ErrorResponder.fill_error(return_obj, response.content, status_code)
                raise Exception(return_obj)
            response_json = json.loads(response.content)
            assets = assets + response_json['sensors']
            offset += 1
            has_more_results = response_json["hasMoreResults"]

        return assets

    def get_vulnerabilities(self, last_model_state_id=None, current_model_state_id=None):
        """
        Fetch the entire vulnerability  records from data source.
        returns:
            results(list): Api response
        """
        headers = self.config['parameter']['headers']
        server_endpoint = self.server + self.config['endpoint']['vulnerability']
        query = json.dumps({"endTime": current_model_state_id})

        if last_model_state_id:
            start_time = current_model_state_id - (int(context().args.malop_retention_period) * 24
                                                   * 60 * 60 * 1000)
            query = json.dumps({"startTime": start_time,
                                "endTime": current_model_state_id})

        response = self.get_collection("POST", server_endpoint, data=query, headers=headers)
        if response.status_code != 200:
            return_obj = {}
            status_code = response.status_code
            ErrorResponder.fill_error(return_obj, response.content, status_code)
            raise Exception(return_obj)

        response_json = json.loads(response.content)
        results = response_json['malops']
        return results

    def network_interface(self, assets=None):
        """
        Fetch the entire netework interface  records from data source.
        returns:
            results(list): Api response
        """
        headers = self.config['parameter']['headers']
        server_endpoint = self.server + self.config['endpoint']['network']
        query = json.dumps({
            "queryPath": [{
                "requestedType": "Machine",
                "guidList": assets,
                "connectionFeature": {
                    "elementInstanceType": "Machine",
                    "featureName": "networkInterfaces"
                }
            },
                {
                    "requestedType": "NetworkInterface",
                    "filters": [],
                    "isResult": True
                }],
            "totalResultLimit": self.config['query_parameter']['result_limit'],
            "perGroupLimit": self.config['query_parameter']['group_limit'],
            "perFeatureLimit": self.config['query_parameter']['feature_limit'],
            "templateContext": "CUSTOM",
            "queryTimeout": self.config['query_parameter']['timeout'],
            "customFields": self.config['query_parameter']['network_fields'],
        })
        response = self.get_collection("POST", server_endpoint, data=query, headers=headers)

        if response.status_code != 200:
            return_obj = {}
            status_code = response.status_code
            ErrorResponder.fill_error(return_obj, response.content, status_code)
            raise Exception(return_obj)

        response_json = json.loads(response.content)
        results = response_json['data']['resultIdToElementDataMap']
        return results

    def get_malop_remediation_status(self, malop_id):
        """
        Fetch the malop remediation from data source.
        returns:
            results(list): Api response
        """
        headers = self.config['parameter']['headers']
        server_endpoint = self.server + self.config['endpoint']['remediation'] + "/" + malop_id
        response = self.get_collection("GET", server_endpoint, data=None, headers=headers)
        if response.status_code != 200:
            return_obj = {}
            status_code = response.status_code
            ErrorResponder.fill_error(return_obj, response.content, status_code)
            raise Exception(return_obj)

        response_json = json.loads(response.content)
        return response_json

    def get_model_state_delta(self, last_model_state_id):
        last_model_state_id = int(float(last_model_state_id))
        # fetch the recent changes
        assets_res = self.get_assets(last_model_state_id)
        assets_guid = []
        if assets_res:
            for asset in assets_res:
                assets_guid.append(asset.get("guid"))
        network_res = self.network_interface(assets=assets_guid)
        # add network information to the asset
        for asset in assets_res:
            mac_list = {}
            for key, value in network_res.items():
                machines = value["elementValues"]["ownerMachine"]["elementValues"]
                for machine in machines:
                    if asset["guid"] == machine["guid"]:
                        if value["simpleValues"].get("macAddressFormat") and \
                                value["simpleValues"]["macAddressFormat"]["values"]:
                            ipaddress_list = value["elementValues"]["ipAddress"]["elementValues"]
                            for ipaddress in ipaddress_list:
                                mac_list[ipaddress["name"]] = value["simpleValues"]["macAddressFormat"]["values"]
            asset["mac_list"] = mac_list
        # add network information to assets
        current_time = get_current_epoch_time()
        vulnerability_res = self.get_vulnerabilities(last_model_state_id=last_model_state_id,
                                                     current_model_state_id=current_time)
        collection_dict = {'asset': assets_res,
                           'vulnerability': vulnerability_res}
        return collection_dict
