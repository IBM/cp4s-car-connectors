import datetime
from car_framework.context import context
from car_framework.data_handler import BaseDataHandler


def timestamp_conv(time_string):
    time_pattern = "%Y-%m-%dT%H:%M:%S"
    epoch = datetime.datetime(1970, 1, 1)
    converted_time = int(((datetime.datetime.strptime(str(time_string)[:19],
                                                      time_pattern) - epoch).total_seconds()) * 1000)
    return converted_time


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry
            self.source = {'_key': context().args.source,
                           'name': "RHACS",
                           'description': 'Red Hat® Advanced Cluster Security for Kubernetes is an enterprise-ready,'
                                          ' Kubernetes-native security solution, equipping organizations to more '
                                          'securely build, deploy, and run cloud-native applications.',
                           'product_link': "https://www.redhat.com/en/technologies/cloud-computing/openshift/"
                                           "advanced-cluster-security-kubernetes"}
            self.report = {'_key': str(self.timestamp),
                           'timestamp': self.timestamp,
                           'type': 'RHACS',
                           'description': 'RHACS reports'}
        return {'source': self.source, 'report': self.report}

    # Handle cluster from data source
    def handle_cluster(self, obj, last_model_state_id=None):
        """create asset object"""
        for cluster in obj['clusters']:
            res = {}
            res['external_id'] = cluster['id']
            res['name'] = cluster['name']
            res['asset_type'] = 'cluster'
            self.add_collection('asset', res, 'external_id')

    # Handle nodes from data source
    def handle_node(self, obj, last_model_state_id=None):
        """create asset object"""
        for node in obj['nodes']:
            res = {}
            res['external_id'] = node['id']
            res['name'] = node['name']
            res['asset_type'] = 'node'
            res['risk'] = node['riskScore']
            res['cluster_id'] = node['clusterId']
            self.add_collection('asset', res, 'external_id')
            # Handle ipaddresses
            self.handle_ipaddress(node, last_model_state_id)
            # Handle components
            self.handle_application(node, last_model_state_id)

    # Handle containers from data source
    def handle_container(self, obj, last_model_state_id=None):
        """create asset & container objects"""
        for item in obj['containers']:
            # Add asset & container CAR node for each container
            res = {}
            if not item['instanceId'].get('id'):
                continue
            res['external_id'] = item['instanceId']['id']
            res['name'] = item['containerName']
            res['image'] = item['imageDigest']
            res['cluster_id'] = item['clusterId']
            self.add_collection('container', res, 'external_id')

            res['asset_type'] = 'container'
            self.add_collection('asset', res, 'external_id')

            # asset_container (node as asset) edge
            nodes = obj.get('nodes')
            for node in nodes:
                if node['name'] == item['instanceId']['node']:
                    asset_container = {'_from_external_id': node['id'],
                                       '_to_external_id': item['instanceId']['id']}
                    self.add_edge('asset_container', asset_container)
                    break

            # Handle image components as application CAR nodes
            self.handle_application(item, last_model_state_id)

            # Handle Ipaddresses
            self.handle_ipaddress(item)

    # Handle application/components from data source
    def handle_application(self, obj, last_model_state_id=None):
        """create application object"""
        # node as a source, add components as application CAR nodes
        if 'applications' in obj:
            for application in obj['applications']:
                res = {}
                res['name'] = application['name']
                res['external_id'] = application['id']
                self.add_collection('application', res, 'external_id')
                # asset application edge
                asset_application = {'_from_external_id': application['clusterId'],
                                     '_to_external_id': application['id']}
                self.add_edge('asset_application', asset_application)
        else:
            # adding components as application(CAR) nodes
            components = []
            add_objects = True
            if obj.get('components'):  # components from source node
                components = obj['scan']['components']
                scan_time = timestamp_conv(obj['scan']['scanTime'])
            elif obj.get('image') and obj['image']['scan']:  # components from pods->container(image)
                components = obj['image']['scan'].get('components', [])
                scan_time = timestamp_conv(obj['image']['scan']['scanTime'])
            else:  # scan (null) case
                add_objects = False
            if last_model_state_id and add_objects:
                if scan_time < last_model_state_id:
                    add_objects = False
            if add_objects:
                for application in components:
                    res = {}
                    res['name'] = application['name']
                    res['external_id'] = '{} {}'.format(application['name'], application['version'])
                    self.add_collection('application', res, 'external_id')

                    # asset application edge
                    asset_application = {}
                    if obj.get('imageDigest'):
                        # container as asset
                        asset_application['_from_external_id'] = obj['instanceId']['id']
                    else:
                        # node as asset
                        asset_application['_from_external_id'] = obj['id']
                    asset_application['_to_external_id'] = '{} {}'.format(application['name'], application['version'])
                    self.add_edge('asset_application', asset_application)
                # handle vulnerability for component
                self.handle_vulnerability(obj, last_model_state_id)

    # Handle accounts from data source
    def handle_account(self, obj, last_model_state_id=None):
        """create account object"""

        central_stockrox = 'central_stackrox_rhacs'

        if not last_model_state_id:         # Adding static asset only in full import
            res = {}
            res['external_id'] = central_stockrox
            res['name'] = central_stockrox
            res['asset_type'] = 'static'
            res['description'] = 'This static asset is used to link with accounts.'
            self.add_collection('asset', res, 'external_id')

        if obj.get("accounts"):
            account_list = obj['accounts']
            for account in account_list:
                res = {}
                res['name'] = account['name']
                res['external_id'] = account['name']
                self.add_collection('account', res, 'external_id')

                # Add asset_account edge (static asset and account)
                asset_account = {'_from_external_id': central_stockrox,
                                 '_to_external_id': account['name']}
                self.add_edge('asset_account', asset_account)

    # Handle users from data source
    def handle_user(self, obj, last_model_state_id=None):
        """create user object"""
        for user_obj in obj['users']:
            res = {}
            res['username'] = user_obj['id']
            res['employee_id'] = user_obj['authProviderId']
            res['external_id'] = user_obj['id']
            self.add_collection('user', res, 'external_id')
            user_account = {'_from_external_id': user_obj['id'],
                            '_to_external_id': user_obj['role']}
            self.add_edge('user_account', user_account)

    # Create vulnerability Object as per CAR data model from data source
    def handle_vulnerability(self, obj, last_model_state_id=None):
        """create vulnerability object"""
        components = []
        if obj.get('components'):  # components from source node
            components = obj['scan']['components']
            asset_id = obj['id']
        elif obj.get('image') and obj['image']['scan']:  # components from pods->container(image)
            components = obj['image']['scan'].get('components', [])
            asset_id = obj['instanceId']['id']

        for component in components:
            for vuln in component['vulns']:
                add_vuln = True
                first_occurrence = vuln["firstSystemOccurrence"]
                if 'NODE_VULNERABILITY' in vuln['vulnerabilityTypes']:
                    first_occurrence = vuln.get("firstNodeOccurrence", first_occurrence)
                elif 'IMAGE_VULNERABILITY' in vuln['vulnerabilityTypes']:
                    first_occurrence = vuln["firstImageOccurrence"]

                if last_model_state_id and last_model_state_id > timestamp_conv(first_occurrence):
                    add_vuln = False
                    if vuln['lastModified'] is not None \
                            and last_model_state_id < timestamp_conv(vuln['lastModified']):
                        add_vuln = True
                if add_vuln:
                    res = {}
                    res['name'] = vuln["cve"]
                    res['external_id'] = vuln["cve"]
                    res["description"] = vuln["summary"]
                    res["disclosed_on"] = first_occurrence
                    res["published_on"] = vuln["publishedOn"]
                    res["updated_on"] = vuln["lastModified"]
                    res["base_score"] = vuln["cvss"]
                    self.add_collection('vulnerability', res, 'external_id')

                    # asset vulnerability edge creation
                    asset_vulnerability = {}
                    asset_vulnerability['_from_external_id'] = asset_id
                    asset_vulnerability['_to_external_id'] = vuln['cve']
                    self.add_edge('asset_vulnerability', asset_vulnerability)

                    # application vulnerability edge, component as application
                    application_vulnerability = {'_from_external_id': component['name'],
                                                 '_to_external_id': vuln['cve']}
                    self.add_edge('application_vulnerability', application_vulnerability)

    # Create ip address Object as per CAR data model from data source
    def handle_ipaddress(self, obj, last_model_state_id=None):
        """create ipaddress object"""
        items = []
        if obj.get("internalIpAddresses"):  # from source node
            asset_id = obj['id']
            items = obj['internalIpAddresses']
            if obj.get("externalIpAddresses"):  # from source node
                items.extend(obj['externalIpAddresses'])
        elif obj.get("containerIps"):  # from pods->container(image) node
            asset_id = obj['instanceId']['id']
            items = obj['containerIps']

        for item in items:
            res = {}
            res['_key'] = item
            self.add_collection('ipaddress', res, '_key')
            asset_ipaddress = {'_from_external_id': asset_id,
                               '_to': res['_key']}
            self.add_edge('asset_ipaddress', asset_ipaddress)

            # ipaddress_container edge, container as container
            if obj.get("containerIps"):  # from pods->container(image) node
                ipaddress_container = {'_from': 'ipaddress/' + item,
                                       '_to_external_id': obj['instanceId']['id']}
                self.add_edge('ipaddress_container', ipaddress_container)
