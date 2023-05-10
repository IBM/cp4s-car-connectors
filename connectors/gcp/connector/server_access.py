import json
import re
import time

from car_framework.context import context
from car_framework.util import DatasourceFailure, ErrorCode
from connector.data_handler import epoch_to_datetime_conv, deep_get, timestamp_conv_tz
from google.cloud import asset_v1, logging_v2
from google.cloud import resourcemanager_v3
from google.cloud import securitycenter
from google.cloud.exceptions import Unauthorized, BadRequest
from google.cloud.logging_v2._gapic import _parse_log_entry
from google.cloud.logging_v2.types import LogEntry
from google.oauth2 import service_account
from google.api_core.exceptions import ResourceExhausted
from googleapiclient import discovery
from googleapiclient.errors import HttpError

MAX_PAGE_SIZE = 1000


class AssetServer:

    def __init__(self):
        # Get server connection arguments from config file
        with open('connector/gcp_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.auth = {'client_email': context().args.CONFIGURATION_AUTH_CLIENT_EMAIL,
                     'private_key': context().args.CONFIGURATION_AUTH_PRIVATE_KEY.replace('\\n', '\n'),
                     'token_uri': self.config['endpoint']['token_uri']}
        self.account_credits = ''
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
        assets = []
        try:
            client = asset_v1.AssetServiceClient(credentials=self.account_credits)
            params = {"parent": 'projects/' + project, "asset_types": [asset_type],
                      "content_type": content_type, "page_size": MAX_PAGE_SIZE}
            while True:
                try:
                    response = client.list_assets(request=params)
                    for page in response.pages:
                        for asset in page.assets:
                            assets.append(json.loads(asset_v1.Asset.to_json(asset)))
                    return assets
                except ResourceExhausted as ex:
                    context().logger.debug("Resource Quota exceeded for asset list api, retrying after 10 sec")
                    if page.next_page_token:
                        params['page_token'] = page.next_page_token
                    time.sleep(10)
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
                        response = json.loads(asset_v1.BatchGetAssetsHistoryResponse.to_json(response))
                    except ResourceExhausted as ex:
                        context().logger.info("Resource Quota exceeded for Asset history api")
                        time.sleep(10)
                        continue
                    except BadRequest as ex:
                        # removing invalid instance details
                        if ex.message and "resources don't exist" in ex.message:
                            resources = re.findall('//.*', ex.message)
                            for resource in resources[0].split(','):
                                history_list.remove(resource)
                            continue
                    break
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
            params = {"parent": "projects/{}/sources/-".format(project), "page_size": MAX_PAGE_SIZE}
            if api_filter:
                params["filter"] = api_filter
            while True:
                try:
                    response = client.list_findings(request=params)
                    for page in response.pages:
                        for finding in page.list_findings_results:
                            result.append(securitycenter.ListFindingsResponse.ListFindingsResult.to_dict(finding))
                    return result
                except ResourceExhausted as ex:
                    context().logger.debug("Resource Quota exceeded for SecurityCenter api, retrying after 10 sec")
                    if page.next_page_token:
                        params['page_token'] = page.next_page_token
                    time.sleep(10)
        except Exception as ex:
            raise DatasourceFailure(ex)

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
            logging_client = \
                logging_v2.services.logging_service_v2.LoggingServiceV2Client(credentials=self.account_credits)
            params = {"resource_names": ["projects/{}".format(project)], "page_size": MAX_PAGE_SIZE}
            if filters:
                params["filter"] = filters
            logs = []
            while True:
                try:
                    # Make the request
                    page_result = logging_client.list_log_entries(request=params)
                    for page in page_result.pages:
                        for entry in page.entries:
                            logs.append(_parse_log_entry(LogEntry.pb(entry)))
                    return logs
                except ResourceExhausted as ex:
                    context().logger.debug("Resource Quota exceeded for logging api, retrying after 10 sec sleep")
                    if page.next_page_token:
                        params['page_token'] = page.next_page_token
                    time.sleep(10)
        except Exception as ex:
            raise DatasourceFailure(ex)

    def get_resource_names_from_log(self, project, last_model_state_id, resource_type, event_type):
        """
        Fetch the resource names from logs based on lifecycle operations.
        parameters:
            project(str): project name
            last_model_state_id(int): Last run time(epoch time)
            resource_type(str): type of the resource, supported types are [ vm_instance, web_app, web_app_service,
                                web_app_service_version]
            event_type(str): type of event log, supported types are [ create, update, delete ]
        returns:
            resource_name(list): list of resource names
        """
        resource_names = set()
        time_filter = f' AND timestamp>="{epoch_to_datetime_conv(last_model_state_id)}"'
        logs = self.get_logs(project,
                             self.config['log_filter'][event_type][resource_type] + time_filter)
        for log in logs:
            resource_name = deep_get(log, ['protoPayload', 'resourceName'])
            resource_name = self.config['asset_name_prefix'][resource_type] + resource_name
            if resource_type == 'vm_instance':
                resource_id = deep_get(log, ['resource', 'labels', 'instance_id'])
                if not resource_id:
                    continue
                resource_name = re.sub("instances/.*", "instances/" + resource_id, resource_name)
            resource_names.add(resource_name)
        return resource_names

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
            vm_instance_list = self.get_asset_list(project, self.config['asset_type']['vm_instance'],
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
            vm_instances_pkgs = self.get_asset_list(project, self.config['asset_type']['vm_instance'],
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

    def get_web_applications(self, project):
        """
        Fetch the App Engine application records from data source.
        parameters:
            project(str): project name
        returns:
            application(list): application list
        """
        application = self.get_asset_list(project, self.config['asset_type']['web_app'],
                                          asset_v1.ContentType.RESOURCE)
        return application

    def get_web_app_services(self, project):
        """
        Fetch the App Engine application services records from data source.
        parameters:
            project(str): project name
        returns:
            services(list): services list
        """
        services = self.get_asset_list(project, self.config['asset_type']['web_app_service'],
                                       asset_v1.ContentType.RESOURCE)
        return services

    def get_web_app_service_versions(self, project):
        """
        Fetch the App Engine application service version records from data source.
        parameters:
            project(str): project name
        returns:
            versins(list): versions list
        """
        versions = self.get_asset_list(project, self.config['asset_type']['web_app_service_version'],
                                       asset_v1.ContentType.RESOURCE)
        return versions

    def get_web_app_services_versions(self, project, last_model_state_id=None):
        """
        Get created/updated/deleted App Engine service and version names from logs
        parameters:
            project(str): project name
            last_model_state_id(int): Last run time(epochtime)
        returns:
            resource_names(list): resource names
        """
        resource_names = {"updated_versions": set(), "updated_services": set(),
                          "deleted_versions": set(), "deleted_services": set(),
                          "created_versions": set()}
        time_filter = f'timestamp>="{epoch_to_datetime_conv(last_model_state_id)}"'
        logs = self.get_logs(project, time_filter + ' AND '
                             + '(' + self.config['log_filter']['update']['web_app_service'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['web_app_service'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['create']['web_app_service_version'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['update']['web_app_service_version'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['web_app_service_version'] + ')')
        for log in logs:
            method_name = deep_get(log, ['protoPayload', 'methodName'])
            item = self.config['asset_name_prefix']['web_app'] + deep_get(log, ['protoPayload', 'resourceName'])
            if "CreateVersion" in method_name:
                resource_names['created_versions'].add(item)
            elif 'UpdateVersion' in method_name:
                if item not in resource_names['created_versions']:
                    resource_names['updated_versions'].add(item)
            elif 'DeleteVersion' in method_name:
                if item in resource_names['created_versions']:
                    resource_names['created_versions'].remove(item)
                elif item in resource_names['updated_versions']:
                    resource_names['updated_versions'].remove(item)
                    resource_names['deleted_versions'].add(item)
                else:
                    resource_names['deleted_versions'].add(item)
            elif 'UpdateService' in method_name:
                resource_names['updated_services'].add(item)
                if item in resource_names['deleted_services']:
                    resource_names['deleted_services'].remove(item)
            elif 'DeleteService' in method_name:
                if item in resource_names['updated_services']:
                    resource_names['updated_services'].remove(item)
                resource_names['deleted_services'].add(item)
        return resource_names

    def get_gke_cluster(self, project):
        """
        Fetch the GKE cluster records from data source.
        parameters:
            project(str): project name
        returns:
            clusters(list): cluster list
        """
        clusters = self.get_asset_list(project, self.config['asset_type']['cluster'],
                                       asset_v1.ContentType.RESOURCE)
        return clusters

    def get_gke_nodes(self, project):
        """
        Fetch the GKE Node records from data source.
        parameters:
            project(str): project name
        returns:
            nodes(list): nodes list
        """
        nodes = self.get_asset_list(project, self.config['asset_type']['cluster_node'],
                                    asset_v1.ContentType.RESOURCE)
        return nodes

    def get_gke_pods(self, project):
        """
        Fetch the GKE pod records from data source.
        parameters:
            project(str): project name
        returns:
            pods(list): pods list
        """
        pods = self.get_asset_list(project, self.config['asset_type']['pod'],
                                   asset_v1.ContentType.RESOURCE)
        return pods

    def get_gke_deployments(self, project):
        """
        Fetch the GKE deployment records from data source.
        parameters:
            project(str): project name
        returns:
            deployments(list): deployment list
        """
        deployments = self.get_asset_list(project, self.config['asset_type']['deployment'],
                                          asset_v1.ContentType.RESOURCE)
        return deployments

    def get_gke_workload_vulnerabilities(self, project, last_model_state_id=None):
        """
        Fetch the GKE deployment vulnerabilities from data source.
        parameters:
            project(str): project name
        returns:
            deployments(list): deployment list
        """
        log_filter = self.config['log_filter']['gke_workload_vuln']
        if last_model_state_id:
            log_filter = log_filter + f' AND timestamp>="{epoch_to_datetime_conv(last_model_state_id)}"'
        logs = self.get_logs(project, log_filter)
        clusters = {}
        for log in logs:
            cluster_name = deep_get(log, ['resource', 'labels', 'cluster_name'])
            if cluster_name not in clusters.keys():
                clusters[cluster_name] = {}
            if deep_get(log, ['jsonPayload', 'vulnerability', 'affectedImages']):
                image_name = deep_get(log, ['jsonPayload', 'vulnerability', 'affectedImages'])[0]
                if image_name not in clusters[cluster_name].keys():
                    clusters[cluster_name][image_name] = []
                vulnerability = deep_get(log, ['jsonPayload', 'vulnerability'])
                clusters[cluster_name][image_name].append(vulnerability)
        return clusters

    def get_gke_changes(self, project, last_model_state_id=None):
        """
        Get incremental created/updated/deleted GKE details from logs
        parameters:
            project(str): project name
            last_model_state_id(int): Last run time(epochtime)
        returns:
            resource_names(dict): resource names
        """
        resource_names = {"new_clusters": set(), "deleted_clusters": set(),
                          "new_nodes": set(), "deleted_nodes": set(),
                          "new_pods": set(), "deleted_pods": {},
                          "new_deployments": set(), "deleted_deployments": {}}
        time_filter = f'timestamp>="{epoch_to_datetime_conv(last_model_state_id)}"'
        logs = self.get_logs(project, time_filter + ' AND '
                             + '(' + self.config['log_filter']['create']['cluster'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['cluster'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['create']['cluster_node'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['cluster_node'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['create']['pod'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['pod'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['create']['deployment'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['deployment'] + ')')
        for log in logs:
            method_name = deep_get(log, ['protoPayload', 'methodName'])
            cluster_name = self.config['asset_name_prefix']['cluster'] + 'projects/' + deep_get(log,
                                                                                                ['resource', 'labels',
                                                                                                 'project_id'])
            if len(deep_get(log, ['resource', 'labels', 'location']).split('-')) > 2:
                cluster_name = cluster_name + '/zones/' + deep_get(log, ['resource', 'labels', 'location'])
            else:
                cluster_name = cluster_name + '/locations/' + deep_get(log, ['resource', 'labels', 'location'])
            cluster_name = cluster_name + '/clusters/' + deep_get(log, ['resource', 'labels', 'cluster_name'])
            resource_id = re.subn('(.*?)/(.*?)/', cluster_name + '/k8s/',
                                  deep_get(log, ['protoPayload', 'resourceName']), 1)[0]
            if 'CreateCluster' in method_name:
                if cluster_name in resource_names["deleted_clusters"]:
                    resource_names["deleted_clusters"].remove(cluster_name)
                resource_names["new_clusters"].add(cluster_name)
            elif 'pods.create' in method_name:
                if resource_id in resource_names['deleted_pods'].keys():
                    resource_names['deleted_pods'].pop(resource_id)
                resource_names['new_pods'].add(resource_id)
            elif 'nodes.create' in method_name:
                if resource_id in resource_names['deleted_nodes']:
                    resource_names['deleted_nodes'].remove(resource_id)
                resource_names['new_nodes'].add(resource_id)
            elif 'pods.delete' in method_name:
                if resource_id in resource_names['new_pods']:
                    resource_names['new_pods'].remove(resource_id)
                else:
                    resource_names['deleted_pods'][resource_id] = log
            elif 'nodes.delete' in method_name:
                if resource_id in resource_names['new_nodes']:
                    resource_names['new_nodes'].remove(resource_id)
                else:
                    resource_names['deleted_nodes'].add(resource_id)
            elif 'deployments.create' in method_name:
                resource_id = resource_id.replace("deployments", 'apps/deployments')
                resource_names['new_deployments'].add(resource_id)
                if resource_id in resource_names['deleted_deployments'].keys():
                    resource_names['deleted_deployments'].pop(resource_id)
            elif 'deployments.delete' in method_name:
                resource_id = resource_id.replace("deployments", 'apps/deployments')
                if resource_id in resource_names['new_deployments']:
                    resource_names['new_deployments'].remove(resource_id)
                else:
                    resource_names['deleted_deployments'][resource_id] = log

            elif 'DeleteCluster' in method_name:
                if cluster_name in resource_names['new_clusters']:
                    resource_names['new_clusters'].remove(cluster_name)
                    resource_names['new_nodes'] = {node for node in resource_names['new_nodes']
                                                   if cluster_name not in node}
                    resource_names['new_pods'] = {pod for pod in resource_names['new_pods'] if cluster_name not in pod}
                    resource_names['new_deployments'] = {deployment for deployment in resource_names['new_deployments']
                                                         if cluster_name not in deployment}
                else:
                    resource_names['deleted_clusters'].add(cluster_name)
        return resource_names

    def get_sql_instances(self, project):
        """
        Fetch the SQL instance records from data source.
        parameters:
            project(str): project name
        returns:
            instances(list): SQL instances list
        """
        instances = self.get_asset_list(project, self.config['asset_type']['sql_instance'],
                                        asset_v1.ContentType.RESOURCE)
        return instances

    def get_sql_instance_databases(self, project, instance_names):
        """
        Fetch the SQL instance database records from data source.
        parameters:
            project(str): project name
            instance_names(list): SQL instances
        returns:
            databases(list): SQL instance database list
        """
        databases = dict()
        try:
            service = discovery.build('sqladmin', 'v1beta4', credentials=self.account_credits,
                                      cache_discovery=False)
            for instance in instance_names:
                try:
                    request = service.databases().list(project=project, instance=instance)
                    response = request.execute()
                    databases[instance] = (response['items'])
                except HttpError as err:
                    if "instance is not running" in err.reason:
                        context().logger.debug("Instance %s not running", instance)
        except Exception as ex:
            raise DatasourceFailure(ex)
        return databases

    def get_sql_instance_users(self, project, instance_names):
        """
        Fetch the SQL instance user records from data source.
        parameters:
            project(str): project name
            instance_names(list): SQL instances
        returns:
            users(list): SQL instance user list
        """
        users = dict()
        try:
            service = discovery.build('sqladmin', 'v1beta4', credentials=self.account_credits,
                                      cache_discovery=False)
            for instance in instance_names:
                try:
                    request = service.users().list(project=project, instance=instance)
                    response = request.execute()
                    users[instance] = response['items']
                except HttpError as err:
                    if "instance is not running" in err.reason:
                        context().logger.debug("Instance %s not running", instance)
        except Exception as ex:
            raise DatasourceFailure(ex)
        return users

    def get_sql_changes(self, project, last_model_state_id=None):
        """
        Get incremental created/updated/deleted SQL details from logs
        parameters:
            project(str): project name
            last_model_state_id(int): Last run time(epochtime)
        returns:
            resource_names(dict): resource names
        """
        resource_names = {"new_instances": set(), "deleted_instances": set(), "updated_instances": set(),
                          "new_databases": set(), "deleted_databases": set(),
                          "new_users": set(), "deleted_users": set()}
        time_filter = f'timestamp>="{epoch_to_datetime_conv(last_model_state_id)}"'
        log_name_filter = \
            "logName:(\"cloudaudit.googleapis.com%2Factivity\" OR \"cloudaudit.googleapis.com%2Fdata_access\")"
        logs = self.get_logs(project, time_filter + ' AND ' + log_name_filter + ' AND '
                             + '(' + self.config['log_filter']['create']['sql_instance'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['sql_instance'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['update']['sql_instance'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['create']['sql_database'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['sql_database'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['create']['sql_user'] + ')' + ' OR '
                             + '(' + self.config['log_filter']['delete']['sql_user'] + ')')
        for log in logs:
            method_name = deep_get(log, ['protoPayload', 'methodName'])
            resource_name = deep_get(log, ['protoPayload', 'resourceName'])
            if 'instances.create' in method_name:
                resource_name = resource_name + '/instances/' + \
                                deep_get(log, ['protoPayload', 'request', 'body', 'name'])
                if resource_name in resource_names["deleted_instances"]:
                    resource_names["deleted_instances"].remove(resource_name)
                resource_names["new_instances"].add(resource_name)
            elif 'instances.update' in method_name:
                if resource_name not in resource_names["new_instances"]:
                    resource_names["updated_instances"].add(resource_name)
            elif 'instances.delete' in method_name:
                if resource_name in resource_names["new_instances"]:
                    resource_names["new_instances"].remove(resource_name)
                    continue
                elif resource_name in resource_names["updated_instances"]:
                    resource_names["updated_instances"].remove(resource_name)
                resource_names["deleted_instances"].add(resource_name)
            elif 'databases.create' in method_name:
                resource_name = resource_name + '/databases/' + \
                                deep_get(log, ['protoPayload', 'request', 'body', 'name'])
                if resource_name in resource_names["deleted_databases"]:
                    resource_names["deleted_databases"].remove(resource_name)
                resource_names["new_databases"].add(resource_name)
            elif 'databases.delete' in method_name:
                if resource_name in resource_names["new_databases"]:
                    resource_names["new_databases"].remove(resource_name)
                else:
                    resource_names['deleted_databases'].add(resource_name)
            elif 'users.create' in method_name:
                resource_name = resource_name + '/users/' + deep_get(log, ['protoPayload', 'request', 'body', 'name'])
                if resource_name in resource_names["deleted_users"]:
                    resource_names["deleted_users"].remove(resource_name)
                resource_names['new_users'].add(resource_name)
            elif 'users.delete' in method_name:
                if resource_name in resource_names['new_users']:
                    resource_names['new_users'].remove(resource_name)
                else:
                    resource_names['deleted_users'].add(resource_name)
        return resource_names

    def get_scc_vulnerability(self, project, last_model_state_id=None, status='ACTIVE'):
        """
        Fetch the instance SCC vulnerability records from data source.
        parameters:
        project(str): project name
        last_model_state_id(int): Last run time(epoch time)
        status(str): vulnerability status
        returns:
        scc_vulnerabilities(list): vulnerability findings
        """
        scc_vulnerabilities = []
        api_filter = f'state = \"{status}\"'
        # Vulnerability filter for resources and vulnerable URLs(Web Security Scanner - App Engine)
        resource_filter = " OR ".join(self.config['scc_vulnerability'].values())
        api_filter = api_filter + ' AND ' + f'({resource_filter})'
        try:
            if last_model_state_id:
                api_filter = api_filter + ' AND ' + f'event_time >= {int(last_model_state_id)}'
            scc_vulnerabilities = self.get_vulnerabilities(project, api_filter)
        except Exception as ex:
            raise DatasourceFailure(ex, ErrorCode.DATASOURCE_FAILURE_DATA_PROCESS.value)
        return scc_vulnerabilities
