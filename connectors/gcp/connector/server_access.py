import json
import re

from car_framework.context import context
from car_framework.util import DatasourceFailure, ErrorCode
from connector.data_handler import epoch_to_datetime_conv, deep_get, timestamp_conv_tz
from google.cloud import asset_v1
from google.cloud import logging
from google.cloud import resourcemanager_v3
from google.cloud import securitycenter
from google.cloud.exceptions import Unauthorized, BadRequest
from google.oauth2 import service_account


class AssetServer:

    def __init__(self):
        # Get server connection arguments from config file
        with open('connector/gcp_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.auth = {'client_email': context().args.client_email,
                     'private_key': context().args.certificate.replace('\\n', '\n'),
                     'token_uri': self.config['endpoint']['token_uri']}
        self.account_credits = ''
        self.page_size = context().args.page_size
        self.asset_vul = {}

    def test_connection(self):
        """test the connection"""
        try:
            projects = self.set_credentials_and_projects()
            if projects:
                code = 0
            else:
                code = 1
        except Exception as e:
            context().logger.error("Test connection failed, error:%s", e)
            code = 1
        return code

    def set_credentials_and_projects(self):
        """
        Set the credentials and Fetch the project list from data source.
        returns:
            result(dict): Project List
        """
        try:
            self.account_credits = service_account.Credentials.from_service_account_info(self.auth)
            client = resourcemanager_v3.ProjectsClient(credentials=self.account_credits)
            request = resourcemanager_v3.SearchProjectsRequest()
            response = client.search_projects(request=request)
            projects = {}
            for project in response:
                projects[project.display_name] = project.name
            return projects

        except Unauthorized as ex:
            raise DatasourceFailure(ex, ErrorCode.DATASOURCE_FAILURE_AUTH.value)
        except Exception as ex:
            raise DatasourceFailure(ex)

    def get_asset_list(self, project, asset_type, content_type):
        """
        Fetch the entire asset records from data source using pagination.
        parameters:
            project(str): project name
            asset_types(str): asset types
        returns:
            result(list): Asset response
        """
        try:
            client = asset_v1.AssetServiceClient(credentials=self.account_credits)
            params = {"parent": 'projects/' + project, "asset_types": [asset_type],
                      "content_type": content_type}
            if self.page_size:
                params["page_size"] = int(self.page_size)
            response = client.list_assets(request=params)
            result = [json.loads(asset_v1.Asset.to_json(res)) for res in response]

            while getattr(response, 'next_page_token'):
                params['page_token'] = response.next_page_token
                response = client.list_assets(request=params)
                result += [json.loads(asset_v1.Asset.to_json(res)) for res in response]
            return result
        except Exception as ex:
            raise DatasourceFailure(ex)

    def get_asset_history(self, project, asset_names, content_type, last_model_state_id):
        """Get the asset history
        parameters:
            project(str): project name
            asset_ids(list): list of asset names
            content_type(asset_v1): asset content type
            last_model_state_id(int): Last run time(epoch time)
        returns:
            asset_list(list): Assets history response
        """
        try:
            asset_list = []
            asset_name_list = []
            client = asset_v1.AssetServiceClient(credentials=self.account_credits)
            asset_ids = list(asset_names)
            start_time = epoch_to_datetime_conv(last_model_state_id)
            for i in range(0, len(asset_ids), 100):
                history_list = asset_ids[i:i + 100]
                while True:
                    params = {"parent": 'projects/' + project, "asset_names": history_list,
                              "content_type": content_type, "read_time_window": {"start_time": start_time}}
                    try:
                        response = client.batch_get_assets_history(request=params)
                    except BadRequest as ex:
                        # removing invalid instance details
                        if ex.message and "resources don't exist" in ex.message:
                            resources = re.findall('//.*', ex.message)
                            for resource in resources[0].split(','):
                                history_list.remove(resource)
                            continue
                    break
                response = json.loads(asset_v1.BatchGetAssetsHistoryResponse.to_json(response))
                if response.get('assets'):
                    for asset in response.get('assets'):
                        # skip deleted asset
                        if asset.get("deleted"):
                            continue
                        if asset['asset']['name'] not in asset_name_list:
                            if timestamp_conv_tz(asset['window']['startTime']) >= last_model_state_id:
                                asset_list.append(asset['asset'])
                                asset_name_list.append(asset['asset']['name'])
            return asset_list
        except Exception as ex:
            raise DatasourceFailure(ex)

    def get_vulnerabilities(self, project, api_filter=None):
        """
        Fetch the entire vulnerability records from data source using pagination.
        parameters:
            project(str): project name
        returns:
            result(list): Vulnerability response
        """
        result = []
        try:
            client = securitycenter.SecurityCenterClient(credentials=self.account_credits)
            params = {"parent": "projects/{}/sources/-".format(project)}
            if api_filter:
                params["filter"] = api_filter
            response = client.list_findings(request=params)
            result = [securitycenter.ListFindingsResponse.ListFindingsResult.to_dict(res) for res in response]

            while getattr(response, 'next_page_token'):
                params['page_token'] = response.next_page_token
                response = client.list_findings(request=params)
                result += [securitycenter.ListFindingsResponse.ListFindingsResult.to_dict(res) for res in response]
        except Exception as ex:
            raise DatasourceFailure(ex)
        return result

    def get_logs(self, project, filters, logger=None):
        """
        Fetch the audit logs from data source.
        parameters:
            project(str): project name
            filters(str): Audit filter
            logger(str): type of logger
        returns:
            result(list): Audit response
        """
        try:
            logging_client = logging.Client(credentials=self.account_credits, project=project)
            if logger:
                logging_client.logger(logger)
            response = logging_client.list_entries(filter_=filters, resource_names=['projects/' + project])
            return [log.to_api_repr() for log in response]

        except Exception as ex:
            raise DatasourceFailure(ex)

    def get_vm_instances(self, project, asset_names=None, last_model_state_id=None):
        """
        Fetch the instance records from data source.
        parameters:
            project(str): project name
            asset_names(list): list of instance names
            last_model_state_id(int): Last run time(epoch time)
        returns:
            vm_instance_list(list): Instance response
        """
        vm_instance_list = []
        if last_model_state_id:
            vm_instance_list = self.get_asset_history(project, asset_names,
                                                      asset_v1.ContentType.RESOURCE,
                                                      last_model_state_id)
        else:
            vm_instance_list = self.get_asset_list(project, self.config['asset_type']['vm'],
                                                   asset_v1.ContentType.RESOURCE)
        return vm_instance_list

    def get_instances_pkgs(self, project, asset_names=None, last_model_state_id=None):
        """
        Fetch the instance os and software records from data source.
        parameters:
            project(str): project name
            asset_names(list): list of instance names
            last_model_state_id(int): Last run time(epoch time)
        returns:
            vm_instances_pkgs(list): Instances OS response
        """
        vm_instances_pkgs = []
        if last_model_state_id:
            vm_instances_pkgs = self.get_asset_history(project, asset_names,
                                                       asset_v1.ContentType.OS_INVENTORY,
                                                       last_model_state_id)
        else:
            vm_instances_pkgs = self.get_asset_list(project, self.config['asset_type']['vm'],
                                                    asset_v1.ContentType.OS_INVENTORY)
        return vm_instances_pkgs

    def get_instance_vulnerabilities(self, project, asset_names=None, last_model_state_id=None):
        """
        Fetch the instance vulnerability records from data source.
        parameters:
            project(str): project name
            asset_names(list): list of instance names
            last_model_state_id(int): Last run time(epochtime)
        returns:
            vm_instance_vuln(list): Instance vulnerability response
        """
        vm_instance_vuln = []
        if last_model_state_id:
            vm_instance_vuln = self.get_asset_history(project, asset_names,
                                                      asset_v1.ContentType.RESOURCE,
                                                      last_model_state_id)
        else:
            vm_instance_vuln = self.get_asset_list(project, self.config['asset_type']['os_pkg_vuln'],
                                                   asset_v1.ContentType.RESOURCE)
        return vm_instance_vuln

    def get_vm_instance_created(self, project, last_model_state_id=None):
        """Get created VM instances names from logs
        parameters:
            project(str): project name
            last_model_state_id(int): Last run time(epochtime)
        returns:
            resource_names(list): resource names
        """
        resource_names = set()
        time_filter = f' AND timestamp>="{epoch_to_datetime_conv(last_model_state_id)}"'
        logs = self.get_logs(project,
                             self.config['asset_create_log_filter']['vm_instance'] + time_filter)
        for log in logs:
            resource_name = deep_get(log, ['protoPayload', 'resourceName'])
            resource_name = self.config['asset_name_prefix']['vm'] + resource_name
            resource_id = deep_get(log, ['protoPayload', 'response', 'targetId'])
            if not resource_id:
                continue
            resource_name = re.sub("instances/.*", "instances/" + resource_id, resource_name)
            resource_names.add(resource_name)
        return resource_names

    def get_vm_instance_updated(self, project, last_model_state_id=None):
        """Get updated VM instances names from logs
        parameters:
            project(str): project name
            last_model_state_id(int): Last run time(epochtime)
        returns:
            resource_names(list): resource names
        """
        resource_names = set()
        time_filter = f' AND timestamp>="{epoch_to_datetime_conv(last_model_state_id)}"'
        logs = self.get_logs(project,
                             self.config['asset_update_log_filter']['vm_instance'] + time_filter)
        for log in logs:
            resource_name = deep_get(log, ['protoPayload', 'resourceName'])
            resource_name = self.config['asset_name_prefix']['vm'] + resource_name
            resource_id = deep_get(log, ['protoPayload', 'response', 'targetId'])
            if not resource_id:
                continue
            resource_name = re.sub("instances/.*", "instances/" + resource_id, resource_name)
            resource_names.add(resource_name)
        return resource_names

    def get_vm_instance_deleted(self, project, last_model_state_id=None):
        """Get deleted VM instances names from logs
        parameters:
            project(str): project name
            last_model_state_id(int): Last run time(epochtime)
        returns:
            resource_names(list): resource names
        """
        resource_names = set()
        time_filter = f' AND timestamp>="{epoch_to_datetime_conv(last_model_state_id)}"'
        logs = self.get_logs(project,
                             self.config['asset_del_log_filter']['vm_instance'] + time_filter)
        for log in logs:
            resource_name = deep_get(log, ['protoPayload', 'resourceName'])
            resource_name = self.config['asset_name_prefix']['vm'] + resource_name
            resource_id = deep_get(log, ['protoPayload', 'response', 'targetId'])
            if not resource_id:
                continue
            resource_name = re.sub("instances/.*", "instances/" + resource_id, resource_name)
            resource_names.add(resource_name)
        return resource_names

    def get_scc_vulnerability(self, project, last_model_state_id=None, status='ACTIVE'):
        """
        Fetch the instance SCC vulnerability records from data source.
        parameters:
        project(str): project name
        last_model_state_id(int): Last run time(epochtime)
        status(str): vulnerability status
        returns:
        scc_vulnerabilities(list): vulnerability findings
        """
        scc_vulnerabilities = []
        api_filter = f'state = \"{status}\"'
        try:
            if last_model_state_id:
                api_filter = api_filter + ' AND ' + f'event_time >= {int(last_model_state_id)}'
            scc_vulnerabilities = self.get_vulnerabilities(project, api_filter)
        except Exception as ex:
            raise DatasourceFailure(ex, ErrorCode.DATASOURCE_FAILURE_DATA_PROCESS.value)
        return scc_vulnerabilities
