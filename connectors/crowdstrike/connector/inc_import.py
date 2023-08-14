from car_framework.context import context
from car_framework.inc_import import BaseIncrementalImport
from connector.data_handler import DataHandler, deep_get, group_host_sensor_apps


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        self.create_source_report_object()
        self.delta = {}
        self.last_model_state_id = ""
        self.update_edge = []
        self.deleted_vertices = {'asset': set(), 'hostname': set(), 'ipaddress': set(),
                                 'account': set(), 'application': set()}

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.last_model_state_id = float(last_model_state_id)

    # Logic to import a collection between two save points; called by import_vertices
    def import_collection(self):
        """
        It will process the api response and does following operations
        Incremental create, Incremental update.
        """
        hosts = context().asset_server.get_hosts(self.last_model_state_id)
        self.compute_inactive_hostname_edges(hosts)
        getattr(self.data_handler, 'handle_asset')(hosts)
        agent_related_asset_ids = {host['aid']: host['id'] for host in hosts if deep_get(host, ['aid'])}
        applications = context().asset_server.get_applications(last_model_state_id=self.last_model_state_id)
        getattr(self.data_handler, 'handle_application')(applications)
        accounts = context().asset_server.get_accounts(self.last_model_state_id)
        account_logins = context().asset_server.get_logins(accounts)
        getattr(self.data_handler, 'handle_account')(account_logins)
        # Handle Incremental vulnerabilities
        agent_applications_map = group_host_sensor_apps(applications)
        vulnerabilities = context().asset_server.get_vulnerabilities(self.last_model_state_id)
        context().asset_server.get_vulnerable_applications(vulnerabilities, agent_applications_map)
        new_vulnerabilities = self.get_incremental_vulnerabilities(vulnerabilities, agent_related_asset_ids)
        getattr(self.data_handler, 'handle_vulnerability')(new_vulnerabilities, agent_related_asset_ids)

    @staticmethod
    def get_active_car_node_fields(resource_type, search_field, comp_operator,  search_value, get_fields):
        """
        It will fetch the active nodes/edges fields from CAR Database based on value of the fields
        returns:
            resource_fields(list) : list of nodes/edges
        """
        # GraphQL query
        resource_fields = []
        query = "{ %s(where: { _and: [{%s: {%s: \"%s\"}},{%s: {_eq: \"%s\"}}]}){%s}}" \
                % (resource_type, search_field, comp_operator, search_value, 'source', context().args.CONNECTION_NAME,
                   ','.join(get_fields))
        result = context().car_service.query_graphql(query)
        if result and deep_get(result, ['data', resource_type]):
            resource_fields = deep_get(result, ['data', resource_type])
        return resource_fields

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

    def get_incremental_vulnerabilities(self, vulnerabilities, agent_related_asset_ids):
        """Handle New and closed vulnerabilities"""
        new_vulnerabilities = []
        for vuln in vulnerabilities:
            agent_id = deep_get(vuln, ['aid'])
            if agent_id not in agent_related_asset_ids:
                asset_id = self.get_active_car_node_fields('asset', 'agent_id', '_eq', agent_id, ['external_id'])
                if asset_id:
                    agent_related_asset_ids[agent_id] = deep_get(asset_id[0], ['external_id'])
            if vuln['status'] in ['open', 'reopen']:
                new_vulnerabilities.append(vuln)
            else:
                # asset_vulnerability edge will be disabled
                asset_id = agent_related_asset_ids[agent_id]
                cve_id = deep_get(vuln, ['cve', 'id'])
                self.updated_edges(asset_id, [cve_id], 'asset_vulnerability')
        return new_vulnerabilities

    def compute_inactive_hostname_edges(self, inc_hosts):
        """ Get the host edges to disable. Get active edges from CAR DB,
        compare host details with CAR and disable hostname edges if not present """
        source = context().args.CONNECTION_NAME
        edges = ['hostname', 'ipaddress']
        for node in edges:
            edge_fields = ['asset_id', node + '_id', 'source']
            result = context().car_service.search_collection('asset_' + node, "source", source, edge_fields)
            if result:
                active_edges = result['asset_' + node]
                active_edges = self.map_asset_edges(active_edges, 'asset_' + node)
                for host in inc_hosts:
                    ext_id = deep_get(host, ['id'])
                    if deep_get(active_edges, [ext_id]):
                        car_ids = deep_get(active_edges, [ext_id])
                        if node == 'hostname':
                            host_name = [deep_get(host, ['hostname'])]
                            self.deleted_vertices['hostname'].update(set(car_ids) - set(host_name))
                        if node == 'ipaddress':
                            ipaddress = []
                            if deep_get(host, ['external_ip']):
                                ipaddress.append(deep_get(host, ['external_ip']))
                            for network in deep_get(host, ['network_interfaces']):
                                ipaddress.append(deep_get(network, ['local_ip']))
                            self.deleted_vertices['ipaddress'].update(set(car_ids) - set(ipaddress))

    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        # can be left as it is if data handler manages the add edge logic
        self.data_handler.send_edges(self)

    def disable_edges(self):
        """ Disable the inactive edges """
        context().logger.info('Disabling edges')
        for edge in self.update_edge:
            context().car_service.edge_patch(context().args.CONNECTION_NAME, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.update_edge))

    def updated_edges(self, from_id, to_ids, edge_type):
        for to_id in to_ids:
            disable_edge = {}
            disable_edge['edge_type'] = edge_type
            disable_edge['from'] = from_id
            disable_edge['to'] = to_id
            if edge_type == "asset_ipaddress":
                disable_edge['to'] = '0/' + to_id
            self.update_edge.append(disable_edge)

    def delete_vertices(self):
        """ Delete vertices and disable inactive edges """
        context().logger.info('Delete vertices started')
        self.disable_edges()

        # Crowdstrike discovery retain the asset, account, application data for 45 days,
        # get asset data from CAR DB which are not updated from last 45 days
        inactive_timestamp = self.data_handler.timestamp - 45 * 24 * 60 * 60 * 1000
        inactive_assets = self.get_active_car_node_fields('asset', 'last_seen_timestamp', '_lte',
                                                          inactive_timestamp, ['external_id'])
        for asset in inactive_assets:
            asset_id = asset['external_id']
            self.deleted_vertices['asset'].add(asset_id)
            from_asset = context().args.CONNECTION_NAME + '/' + asset_id
            host_names = self.get_active_car_node_fields('asset_hostname', 'asset_id', '_eq',
                                                         from_asset, ['hostname_id'])
            for hostname in host_names:
                self.deleted_vertices['hostname'].add(hostname['hostname_id'].split('/', 1)[1])
            host_ipaddress = self.get_active_car_node_fields('asset_ipaddress', 'asset_id', '_eq',
                                                             from_asset, ['ipaddress_id'])
            for ipaddress in host_ipaddress:
                self.deleted_vertices['ipaddress'].add(ipaddress['ipaddress_id'].split('/', 1)[1])

        deleted_accounts = self.get_active_car_node_fields('account', 'last_successful_login_time', '_lte',
                                                           inactive_timestamp, ['external_id'])
        for account in deleted_accounts:
            self.deleted_vertices['account'].add(account['external_id'])
        deleted_applications = self.get_active_car_node_fields('application', 'last_access_time', '_lte',
                                                               inactive_timestamp, ['external_id'])
        for app in deleted_applications:
            self.deleted_vertices['application'].add(app['external_id'])

        for vertices, vertices_list in self.deleted_vertices.items():
            if vertices_list:
                context().car_service.delete(vertices, vertices_list)
        context().logger.info('Deleted vertices done: %s',
                              {key: len(value) for key, value in self.deleted_vertices.items()})
