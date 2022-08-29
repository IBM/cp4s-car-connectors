import json
import requests
from car_framework.context import context
from car_framework.util import DatasourceFailure
from connector.data_handler import timestamp_conv
from connector.error_response import ErrorResponder


class AssetServer:

    def __init__(self):
        # Get server connection arguments from config file
        with open('connector/rhacs_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.image_container = {}  # stores the image and container links
        self.ipaddress_list = []   # list will be used for deletion
        self.container_list = []    # list will be used for deletion
        self.cluster_node_list = []  # list will be used for deletion
        self.user_list = []  # list will be used for deletion

    def test_connection(self):
        """test the connection"""
        try:
            response = self.get_collection(self.config['endpoint']['auth'], False)
            if response.status_code == 200:
                code = 0
            else:
                code = 1
        except DatasourceFailure as e:
            context().logger.error(e)
            code = 1
        return code

    def get_collection(self, asset_server_endpoint, check_status=True):
        """
        Fetch data from datasource using api
        parameters:
            asset_server_endpoint(str): api end point
            check_status(bool): If False, directly return the response
        returns:
            json_data(dict): Api response
        """
        try:
            return_obj = {}
            api_response = requests.get("https://" + context().args.host + asset_server_endpoint,
                                        headers={"Authorization": "Bearer " + context().args.token})

            if not check_status:  # without checking the status code return the response
                return api_response

            if api_response.status_code != 200:
                status_code = api_response.status_code
                ErrorResponder.fill_error(return_obj, api_response.content, status_code)
                raise Exception(return_obj)

            return json.loads(api_response.content)

        except Exception as ex:
            if not return_obj:
                ErrorResponder.fill_error(return_obj, ex)
            raise Exception(return_obj)

    def get_assets(self, last_model_state_id=None):
        """
        Fetch the entire asset records from data source.
        returns: results(list): Api response
        """
        response_json = self.get_collection(self.config['endpoint']['clusters'])
        clusters = []
        nodes = []

        if response_json['clusters']:
            for obj in response_json.get('clusters'):
                node = self.get_collection(self.config['endpoint']['nodes'] + '/' + obj['id'])
                if last_model_state_id:  # inc import
                    self.cluster_node_list.append(obj['id'])    # collecting all cluster & node id
                for node_obj in node["nodes"]:
                    if last_model_state_id:  # inc import
                        self.ipaddress_list += node_obj['internalIpAddresses']
                        self.ipaddress_list += node_obj['externalIpAddresses']      # collecting all ipaddress
                        self.cluster_node_list.append(node_obj['id'])   # collecting all cluster & node id
                    nodes.append(node_obj)
                clusters.append(obj)
                break

        return clusters, nodes

    def get_applications(self, last_model_state_id=None):
        """
        Fetch the entire application records from data source.
        parameters: last_model_state_id(datetime): last run time
        returns: results(list): Api response
        """
        response = self.get_collection(self.config['endpoint']['deployments'])
        application = []

        if last_model_state_id:  # incremental import
            for obj in response.get('deployments'):
                if last_model_state_id < timestamp_conv(obj['created']):
                    application.append(obj)
                break
        else:  # full import
            application = response.get('deployments', [])

        return application

    def get_containers(self, last_model_state_id=None):
        """
        Fetch the container records from data source.
        parameters: last_model_state_id(datetime): last run time
        returns: results(list): Api response
        """
        containers = []
        images = {}

        response = self.get_collection(self.config['endpoint']['containers'])
        container_response = response.get('pods', [])

        for container_obj in container_response:

            # live containers
            for instance_obj in container_obj["liveInstances"]:

                if last_model_state_id:  # inc import
                    self.ipaddress_list += instance_obj['containerIps']         # collecting all ipaddress
                    self.container_list.append(instance_obj['instanceId']['id'])        # collecting all container id's
                    # store then image and container link
                    self.image_container[instance_obj['imageDigest']] = instance_obj['instanceId']['id']

                # incremental run
                if last_model_state_id and \
                        (container_obj['started'] is None or
                         last_model_state_id > timestamp_conv(container_obj['started'])):
                    continue

                if not images.get(instance_obj['imageDigest']):
                    if instance_obj['imageDigest']:
                        response = self.get_collection(
                            self.config['endpoint']['images'] + '/' + instance_obj['imageDigest'], False)
                        if response.status_code == 200:
                            images[instance_obj['imageDigest']] = json.loads(response.content)

                instance_obj['image'] = images.get(instance_obj['imageDigest'], '')
                instance_obj['clusterId'] = container_obj.get('clusterId', '')
                containers.append(instance_obj)
            break

        return containers

    def get_account_users(self, last_model_state_id=None):
        """
        Fetch the account and user records from data source.
        parameters: last_model_state_id(datetime): last run time
        returns: results(list): Api response
        """
        users = []
        group = {}

        response = self.get_collection(self.config['endpoint']['roles'])
        accounts = response.get('roles', [])

        response = self.get_collection(self.config['endpoint']['groups'])
        group_response = response.get('groups', [])
        for group_obj in group_response:
            group[group_obj['props']['authProviderId']] = group_obj['roleName']

        response = self.get_collection(self.config['endpoint']['users'])
        user_response = response.get('users', [])

        for user_obj in user_response:
            temp = {
                'id': user_obj['id'],
                'authProviderId': user_obj['authProviderId'],
                'role': group.get(user_obj['authProviderId'], '')
            }
            users.append(temp)

            if last_model_state_id:
                self.user_list.append(user_obj['id'])

        return accounts, users

    def get_data_source(self, last_model_state_id=None):
        """
        Fetch the entire records from data source.
        parameters: last_model_state_id(datetime): last run time
        returns: collection(dict): collection of api responses
                 terminated_containers(list): terminated containers ip
        """
        clusters, nodes = self.get_assets(last_model_state_id)
        applications = self.get_applications(last_model_state_id)
        containers = self.get_containers(last_model_state_id)
        accounts, users = self.get_account_users(last_model_state_id)

        collections = {'clusters': clusters, 'nodes': nodes, 'applications': applications,
                       'containers': containers, 'accounts': accounts, 'users': users}

        # Incremental import
        if last_model_state_id:
            asset_list = {'container_list': self.container_list,
                          'ipaddress_list': set(self.ipaddress_list),
                          'cluster_node_list': self.cluster_node_list,
                          'user_list': self.user_list}
            return collections, asset_list

        # Full import
        return collections

    def get_deferred_vulnerability(self, last_model_state_id=None):
        """
        Fetch the deferred vulnerability records from data source.
        parameters: last_model_state_id(datetime): last run time
        returns: results(list): Api response
        """
        response = self.get_collection(self.config['endpoint']['defer_cve'])
        images = self.get_collection(self.config['endpoint']['images'])
        edges = []

        for obj in response['requestInfos']:
            if obj['status'] == 'APPROVED' and \
                    last_model_state_id < timestamp_conv(obj['lastUpdated']):

                image_name = obj['scope']['imageScope']['registry'] + '/' + obj['scope']['imageScope']['remote']

                # Finding the image id
                image_id = ""
                for img in images['images']:
                    if image_name in img['name']:
                        image_id = img['id']
                        break

                # inactive asset_vulnerability edges
                if self.image_container.get(image_id):
                    temp = {
                        'from': self.image_container.get(image_id),
                        'to': obj['cves']['ids'][0],
                        'edge_type': 'asset_vulnerability'}

                    edges.append(temp)
            break
        return edges
