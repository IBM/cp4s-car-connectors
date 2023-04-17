import re

from car_framework.context import context
from car_framework.inc_import import BaseIncrementalImport
from connector.data_handler import DataHandler, deep_get
from google.cloud import asset_v1


def get_asset_name_from_assets(assets):
    """ Get the asset names from asset details"""
    return [asset['name'] for asset in assets]


def construct_os_vuln_report_names(assets):
    """ Construct os vulnerability report asset names from instance names"""
    vuln_report_names = []
    # asset_names = get_asset_name_from_assets(assets)
    for asset in assets:
        asset_id = deep_get(asset, ['name'])
        asset_id = asset_id.replace(deep_get(asset, ['resource', 'data', 'name']),
                                    deep_get(asset, ['resource', 'data', 'id']))
        asset_id = re.sub("compute.", "osconfig.", asset_id)
        project_id = deep_get(asset, ['ancestors'])[0]
        asset_id = re.sub("projects/.*?/", project_id + '/', asset_id)
        asset_id = re.sub("zones/", "locations/", asset_id)
        asset_id = asset_id + '/vulnerabilityReport'
        vuln_report_names.append(asset_id)
    return vuln_report_names


def get_host_names(instances):
    """ List the hostnames from instance details"""
    hostnames = []
    if not isinstance(instances, list):
        instances = [instances]
    for instance in instances:
        # Include instance name and DNS name
        hostnames.append(deep_get(instance, ['resource', 'data', 'name']))
        if deep_get(instance, ['resource', 'data', 'hostname']):
            hostnames.append(deep_get(instance, ['resource', 'data', 'hostname']))
    return hostnames


def get_ip_address(instances):
    """Lists the ipaddress of the assets"""
    ipaddresses = []
    if not isinstance(instances, list):
        instances = [instances]
    for instance in instances:
        network = deep_get(instance, ['resource', 'data', 'networkInterfaces'], [])
        ipaddress = []
        for interface in network:
            if deep_get(interface, ['ipv6Address']):
                ipaddress.append(deep_get(interface, ['ipv6Address']))
            if deep_get(interface, ['networkIP']):
                ipaddress.append(deep_get(interface, ['networkIP']))
            if deep_get(interface, ['accessConfigs']):
                for config in deep_get(interface, ['accessConfigs']):
                    if config.get('natIP'):
                        ipaddress.append(config.get('natIP'))
            if deep_get(interface, ['ipv6AccessConfigs']):
                for config in deep_get(interface, ['ipv6AccessConfigs']):
                    if config.get('natIP'):
                        ipaddress.append(config.get('natIP'))
        ipaddresses += ipaddress
    return ipaddresses


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        self.create_source_report_object()
        self.delta = {}
        self.last_model_state_id = ""
        self.asset_list = {}
        self.vm_instances = []
        self.deleted_vertices = {'asset': set(), 'hostname': set(), 'ipaddress': set(),
                                 'application': set(), 'vulnerability': set()}
        self.update_edge = []
        self.projects = []
        self.deleted_vulnerabilities = []

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        # There is some delay in GCP Audit logs update, when an event occurs (eg: update name of VM)
        # due to which during incremental import some logs are missing.
        # Hence, keeping 60 sec before the last runtime to avoid missing logs.
        self.last_model_state_id = float(last_model_state_id) - int(60000)

    # Logic to import a collection between two save points; called by import_vertices
    def import_collection(self):
        """
        It will process the api response and does following operations
        Incremental create, Incremental update.
        """
        self.projects = context().asset_server.set_credentials_and_projects()
        for project, project_name in self.projects.items():
            # VM instances
            self.incremental_vm_instances(project, project_name)
            # App Engine Service handling
            app_hostname, service_name = self.incremental_web_applications(project)
            # scc vulnerability handling
            vulnerability = context().asset_server.get_scc_vulnerability(project, self.last_model_state_id)
            getattr(self.data_handler, 'handle_scc_vulnerability')(vulnerability, service_name, app_hostname)

    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        # can be left as it is if data handler manages the add edge logic
        self.data_handler.send_edges(self)

    def updated_edges(self, from_id, to_ids, edge_type):
        for to_id in to_ids:
            disable_edge = {}
            disable_edge['edge_type'] = edge_type
            disable_edge['from'] = from_id
            disable_edge['to'] = to_id
            if edge_type == "asset_ipaddress":
                disable_edge['to'] = '0/' + to_id
            self.update_edge.append(disable_edge)

    def disable_edges(self):
        """ Disable the inactive edges """
        context().logger.info('Disabling edges')
        for edge in self.update_edge:
            context().car_service.edge_patch(context().args.source, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.update_edge))

    @staticmethod
    def get_active_car_edges(edge):
        """
        It will fetch the active edges from CAR Database
        returns:
            active_edges(list) : list of edges
        """
        active_edges = []
        source = context().args.source
        edge_from, edge_to = edge.split("_")
        from_id = edge_from + "_id"
        to_id = edge_to + "_id"
        edge_fields = [from_id, to_id, 'source']
        result = context().car_service.search_collection(edge, "source", source, edge_fields)
        if result:
            active_edges = result[edge]
        return active_edges

    @staticmethod
    def map_asset_edges(active_edges, edge_name):
        """
        lists all edges  of the asset
        params: active edges(list) and edge name
        return: asset_edges(dict)
        """
        edge_from, edge_to = edge_name.split("_")
        from_id = edge_from + "_id"
        to_id = edge_to + "_id"
        asset_edges = {}
        for edge in active_edges:
            if edge:
                node_1 = edge[from_id].split('/', 1)[1]
                if to_id == 'ipaddress_id':
                    node_2 = edge[to_id].split('/', 2)[2]
                else:
                    node_2 = edge[to_id].split('/', 1)[1]

                if node_1 in asset_edges:
                    asset_edges[node_1].extend([node_2])
                else:
                    asset_edges[node_1] = [node_2]

        return asset_edges

    def incremental_vm_instances(self, project, project_name):
        """Handling VM instances incremental create, update """
        # resource type
        resource_type = 'vm_instance'
        deleted_instances = context().asset_server.get_resource_names_from_log(project, self.last_model_state_id,
                                                                               resource_type, event_type='delete')
        # Incremental create
        new_instances_created = context().asset_server.get_resource_names_from_log(project, self.last_model_state_id,
                                                                                   resource_type, event_type='create')
        # remove deleted instances
        new_instances = new_instances_created - deleted_instances
        created_instances = context().asset_server.get_vm_instances(project, list(new_instances),
                                                                    self.last_model_state_id)
        getattr(self.data_handler, 'handle_vm_instances')(created_instances)
        new_vm_software_pkgs = context().asset_server.get_instances_pkgs(project, list(new_instances),
                                                                         self.last_model_state_id)
        getattr(self.data_handler, 'handle_vm_software_pkgs')(new_vm_software_pkgs)
        vm_vuln_resource_ids = construct_os_vuln_report_names(created_instances)
        new_vm_vulnerabilities = context().asset_server.get_instance_vulnerabilities(project, vm_vuln_resource_ids,
                                                                                     self.last_model_state_id)
        getattr(self.data_handler, 'handle_vm_vulnerabilities')(new_vm_vulnerabilities, project)

        # Incremental update
        updated_instances = context().asset_server.get_resource_names_from_log(project, self.last_model_state_id,
                                                                               resource_type, event_type='update')
        # remove deleted and newly created instances from update list
        updated_instances = updated_instances - set(list(new_instances) + list(deleted_instances))
        updated_assets = context().asset_server.get_asset_history(project, list(updated_instances),
                                                                  asset_v1.ContentType.RESOURCE,
                                                                  self.last_model_state_id)
        getattr(self.data_handler, 'handle_vm_instances')(updated_assets)
        # deleted instances
        deleted_instances = deleted_instances - new_instances_created
        deleted_instances = [name.replace('//', '') for name in deleted_instances]
        self.deleted_vertices['asset'].update(deleted_instances)
        self.compute_inactive_vm_edges(list(updated_assets), list(new_instances), deleted_instances)

        package_updated_instances = self.compute_os_package_updated_instances(project)
        getattr(self.data_handler, 'handle_vm_software_pkgs')(package_updated_instances)
        vulnerability_updated_instances = self.compute_os_vuln_updated_instances(project, project_name)
        getattr(self.data_handler, 'handle_vm_vulnerabilities')(vulnerability_updated_instances, project)

    def compute_inactive_vm_edges(self, updated_instances, new_instances, deleted_instances):
        """ Get the vm edges to disable. Get active edges from CAR DB,
        compare instance details with CAR and disable hostname,ipaddress edges
         if not present """
        new_host_names = get_host_names(updated_instances + new_instances)
        new_ip_addresses = get_ip_address(updated_instances + new_instances)
        for edge in ['asset_hostname', 'asset_ipaddress']:
            active_edge = self.get_active_car_edges(edge)
            edges = self.map_asset_edges(active_edge, edge)
            for instance in updated_instances + deleted_instances:
                asset_id = instance
                # for updated instance has complete details in dictionary
                # and deleted instance is just name
                if isinstance(instance, dict):
                    asset_id = deep_get(instance, ['name'])
                    asset_id = asset_id.replace(deep_get(instance, ['resource', 'data', 'name']),
                                                deep_get(instance, ['resource', 'data', 'id']))
                    asset_id = asset_id.replace("//", '')
                instance_edges = edges.get(asset_id, [])
                # handle hostname
                if edge == 'asset_hostname' and instance_edges:
                    host_name = []
                    if isinstance(instance, dict):
                        host_name = get_host_names(instance)
                    instance_edges = set(instance_edges) - set(host_name)
                    if instance_edges:
                        if instance_edges - set(new_host_names):
                            self.deleted_vertices['hostname'].update(instance_edges)
                        else:
                            self.updated_edges(asset_id, instance_edges, 'asset_hostname')
                if edge == 'asset_ipaddress' and instance_edges:
                    ipaddress = []
                    if isinstance(instance, dict):
                        ipaddress = get_ip_address(instance)
                    instance_edges = set(instance_edges) - set(ipaddress)
                    if instance_edges:
                        if instance_edges - set(new_ip_addresses):
                            self.deleted_vertices['ipaddress'].update(instance_edges)
                        else:
                            self.updated_edges(asset_id, instance_edges, 'asset_ipaddress')

    def compute_os_package_updated_instances(self, project):
        """ Get the asset_application edges to disable. Get active edges from CAR DB,
        compare instance details with CAR and disable edge if not present """
        asset_application_edges = self.get_active_car_edges("asset_application")
        vm_instances = [edge['asset_id'].split('/', 1)[1] for edge in asset_application_edges if
                        "compute." in edge['asset_id']]
        vm_instances = list(set(vm_instances))
        vm_instances = ["//" + vm_instance for vm_instance in vm_instances]
        updated_instances = context().asset_server.get_asset_history(project, vm_instances,
                                                                     asset_v1.ContentType.OS_INVENTORY,
                                                                     self.last_model_state_id)
        for instance in updated_instances:
            asset_name = deep_get(instance, ['name'])
            if not deep_get(instance, ['osInventory']):
                continue
            asset_id = re.findall('instances/.*?/', deep_get(instance, ['osInventory', 'name']))
            asset_id = asset_id[0][:-1]
            asset_name = re.sub('instances/.*', asset_id, asset_name)
            asset_name = asset_name.replace("//", '')
            edges = self.map_asset_edges(asset_application_edges, "asset_application")
            instance_edges = edges.get(asset_name, [])
            applications = []
            applications.append(deep_get(instance, ['osInventory', 'osInfo', 'kernelVersion']))
            for key in deep_get(instance, ['osInventory', 'items']).keys():
                applications.append(key.split('-', 1)[1])
            deleted_apps = set(instance_edges) - set(applications)
            self.updated_edges(asset_name, deleted_apps, 'asset_application')
        return updated_instances

    def compute_os_vuln_updated_instances(self, project, project_name):
        """ Get the asset_vulnerability edges to disable. Get active edges from CAR DB,
        compare instance details with CAR and disable edge if not present """
        asset_vuln_edges = self.get_active_car_edges("asset_vulnerability")
        vm_instances = [edge['asset_id'].split('/', 1)[1] for edge in asset_vuln_edges if
                        "compute." in edge['asset_id'] and "findings" not in edge['vulnerability_id']]
        vm_instances = list(set(vm_instances))
        vuln_instances_list = []
        for vm_instance in vm_instances:
            # constructing vulnerability asset name from instance name
            vm_instance = re.sub('projects/.*?/', project_name + '/', vm_instance)
            vm_instance = re.sub('zones', 'locations', vm_instance)
            vm_instance = re.sub('compute', '//osconfig', vm_instance)
            vm_instance = vm_instance + '/vulnerabilityReport'
            vuln_instances_list.append(vm_instance)
        updated_instances = context().asset_server.get_asset_history(project, vuln_instances_list,
                                                                     asset_v1.ContentType.RESOURCE,
                                                                     self.last_model_state_id)
        for instance in updated_instances:
            if not deep_get(instance, ['resource', 'data']):
                continue
            asset_name = deep_get(instance, ['resource', 'data', 'name'])
            asset_name = re.sub('projects/.*?/', 'projects/' + project + '/', asset_name)
            asset_id = re.sub('/vulnerabilityReport*', '', asset_name)
            asset_id = re.sub('locations', 'zones', asset_id)
            asset_id = "compute.googleapis.com/" + asset_id
            edges = self.map_asset_edges(asset_vuln_edges, "asset_vulnerability")
            instance_edges = edges.get(asset_id, [])
            # remove scc related vulnerabilities
            instance_edges = [vuln for vuln in instance_edges if 'findings/' not in vuln]
            vulnerabilities = [vuln['details']['cve'] for vuln in
                               deep_get(instance, ['resource', 'data', 'vulnerabilities'])]

            deleted_vulnerabilities = set(instance_edges) - set(vulnerabilities)
            self.updated_edges(asset_name, deleted_vulnerabilities, 'asset_vulnerability')
        return updated_instances

    def incremental_web_applications(self, project):
        """Incremental application handling"""
        resource_type = 'web_app'
        new_apps = context().asset_server.get_resource_names_from_log(project, self.last_model_state_id, resource_type,
                                                                      event_type='create')
        if new_apps:
            web_apps = context().asset_server.get_web_applications(project)
            app_hostname = deep_get(web_apps[0], ['resource', 'data', 'defaultHostname'])
            web_app_services = context().asset_server.get_web_app_services(project)
            getattr(self.data_handler, 'handle_web_app_services')(web_app_services, web_apps)
            web_app_service_versions = context().asset_server.get_web_app_service_versions(project, )
            getattr(self.data_handler, 'handle_web_app_service_versions')(web_app_service_versions)
            web_service_names = [service['name'] for service in web_app_services]
            return app_hostname, web_service_names

        web_app = context().asset_server.get_web_applications(project)
        app_hostname = deep_get(web_app[0], ['resource', 'data', 'defaultHostname'])
        services_versions = context().asset_server.get_web_app_services_versions(project, self.last_model_state_id)
        if services_versions['updated_services']:
            updated_services = context().asset_server.get_asset_history(project, services_versions['updated_services'],
                                                                        asset_v1.ContentType.RESOURCE,
                                                                        self.last_model_state_id)
            getattr(self.data_handler, 'handle_web_app_services')(updated_services, web_app)
        versions = services_versions['updated_versions'] | services_versions['created_versions']
        if versions:
            updated_versions = context().asset_server.get_asset_history(project, versions,
                                                                        asset_v1.ContentType.RESOURCE,
                                                                        self.last_model_state_id)
            getattr(self.data_handler, 'handle_web_app_service_versions')(updated_versions)
        # Deleted service and versions
        deleted_services = [name.replace('//', '') for name in services_versions['deleted_services']]
        self.deleted_vertices['asset'].update(deleted_services)
        # delete hostname vertices
        service_host_names = [name.split('/')[-1] + '-dot-' + app_hostname for name in deleted_services]
        self.deleted_vertices['hostname'].update(service_host_names)
        deleted_versions = [name.replace('//', '') for name in services_versions['deleted_versions']]
        self.deleted_vertices['application'].update(deleted_versions)
        return app_hostname, services_versions['updated_services']

    def delete_vertices(self):
        """ Delete asset and disable the inactive asset_vulnerability edges. """
        # delete asset and disable vulnerability edges#
        context().logger.info('Delete vertices started')
        for project in self.projects:
            self.disable_edges()
            # Delete inactive vulnerabilities
            vulnerability = context().asset_server.get_scc_vulnerability(project, self.last_model_state_id,
                                                                         status="INACTIVE")
            deleted_vulnerabilities = [deep_get(vuln, ['finding', 'canonical_name']) for vuln in vulnerability]
            self.deleted_vertices['vulnerability'] = deleted_vulnerabilities
            for vertices, vertices_list in self.deleted_vertices.items():
                if vertices_list:
                    context().car_service.delete(vertices, vertices_list)
        context().logger.info('Deleted vertices done: %s',
                              {key: len(value) for key, value in self.deleted_vertices.items()})
