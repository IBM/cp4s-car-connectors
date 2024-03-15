from car_framework.context import context
from car_framework.inc_import import BaseIncrementalImport
from connector.data_handler import DataHandler, deep_get, update_app_with_cpe


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        self.create_source_report_object()
        self.delta = {}
        self.last_model_state_id = ""
        self.update_edge = []
        self.deleted_vertices = {'asset': set(), 'ipaddress': set(), 'macaddress': set(),
                                 'application': set(), 'vulnerability': set()}

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
        # Incremental filter conditions for Data source queries
        asset_node_filter = f'where last_activity_time > "{int(self.last_model_state_id)}"'
        vuln_filter = f'where time > "{int(self.last_model_state_id)}" | where resolved=="false"'

        assets = context().asset_server.get_query_results(category='asset', query_filter=asset_node_filter)
        sensors = context().asset_server.get_query_results(category='sensor')
        sensors = {value['host']: value for value in sensors}
        getattr(self.data_handler, 'handle_nozomi_assets')(assets, sensors)
        nodes = context().asset_server.get_query_results(category='node', query_filter=asset_node_filter)
        getattr(self.data_handler, 'handle_nozomi_nodes')(nodes)
        # Getting complete list of asset_softwares and software_list
        software_list = context().asset_server.get_query_results(category='software_list')
        applications = context().asset_server.get_query_results(category='asset_softwares')
        update_app_with_cpe(applications, software_list)
        getattr(self.data_handler, 'handle_nozomi_applications')(applications)
        vulnerabilities = context().asset_server.get_query_results(category='asset_cve', query_filter=vuln_filter)
        getattr(self.data_handler, 'handle_nozomi_vulnerabilities')(vulnerabilities)
        getattr(self.data_handler, 'handle_nozomi_app_vuln')(applications, vulnerabilities)

        # Handle Asset updates like,delete old IP if IP address changes,
        # delete old Mac address if mac changes, disable asset_application edge if application are uninstalled.
        inc_updated_assets = [asset for asset in assets
                              if deep_get(asset, ['created_at']) < self.last_model_state_id]
        self.compute_inactive_asset_nodes(inc_updated_assets)

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

    def compute_inactive_asset_nodes(self, assets):
        """ Get the asset nodes to be deleted. Get active edges from CAR DB,
        compare asset details with CAR and delete respective nodes if not present """
        source = context().args.CONNECTION_NAME
        edges = ['ipaddress', 'macaddress', 'application', 'geolocation']
        for node in edges:
            edge_fields = ['asset_id', node + '_id', 'source']
            result = context().car_service.search_collection('asset_' + node, "source", source, edge_fields)
            if result:
                active_edges = result['asset_' + node]
                active_edges = self.map_asset_edges(active_edges, 'asset_' + node)
                for asset in assets:
                    asset_id = deep_get(asset, ['id'])
                    if deep_get(active_edges, [asset_id]):
                        car_ids = deep_get(active_edges, [asset_id])
                        if node == 'ipaddress':
                            ipaddress = []
                            if deep_get(asset, ['ip']):
                                ipaddress.extend(deep_get(asset, ['ip']))
                            self.deleted_vertices['ipaddress'].update(set(car_ids) - set(ipaddress))
                        if node == 'macaddress':
                            macaddress = []
                            if deep_get(asset, ['mac_address']):
                                macaddress.extend(deep_get(asset, ['mac_address']))
                            self.deleted_vertices['macaddress'].update(set(car_ids) - set(macaddress))
                        if node == 'geolocation':
                            locations = [key.split('#', 1)[1] for key in self.data_handler.edge_keys['asset_geolocation']
                                         if asset_id in key]
                            inactive_edges = set(car_ids) - set(locations)
                            self.updated_edges(asset_id, inactive_edges, 'asset_geolocation')
                            # disable ipaddress_geolocation edge
                            if inactive_edges and deep_get(asset, ['ip']):
                                for ip in deep_get(asset, ['ip']):
                                    self.updated_edges(ip, inactive_edges, 'ipaddress_geolocation')
                        if node == 'application':
                            applications = [key.split('#', 1)[1] for key in self.data_handler.edge_keys['asset_application']
                                            if asset_id in key]
                            self.updated_edges(asset_id, set(car_ids) - set(applications), 'asset_application')

    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        # can be left as it is if data handler manages the add edge logic
        self.data_handler.send_edges(self)

    def delete_inactive_assets_associations(self, retention_timestamp):
        # Get the asset ids from CAR DB, assets which are not active based on retention period.
        inactive_assets = self.get_active_car_node_fields('asset', 'last_activity_time', '_lte',
                                                          int(retention_timestamp), ['external_id'])
        # asset and associated nodes
        for asset in inactive_assets:
            asset_id = asset['external_id']
            self.deleted_vertices['asset'].add(asset_id)
            from_asset = context().args.CONNECTION_NAME + '/' + asset_id
            for node in ['ipaddress', 'macaddress', 'vulnerability']:
                edges = self.get_active_car_node_fields(f'asset_{node}', 'asset_id', '_eq',
                                                        from_asset, [f'{node}_id'])
                for edge in edges:
                    if node == "ipaddress":
                        self.deleted_vertices[node].add(edge[f'{node}_id'].split('/', 2)[2])
                    else:
                        self.deleted_vertices[node].add(edge[f'{node}_id'].split('/', 1)[1])

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
        resolved_vuln_filter = f'where closed_time > "{int(self.last_model_state_id)}" | where status=="resolved"'
        deleted_vulnerabilities = context().asset_server.get_query_results(category='vulnerability',
                                                                           query_filter=resolved_vuln_filter)
        for vulnerability in deleted_vulnerabilities:
            self.deleted_vertices['vulnerability'].add(vulnerability['id'])

        # Delete asset and associated nodes based on retention period.
        # Retention period comes in days, converting days to milliseconds.
        retention_timestamp = \
            self.data_handler.timestamp - context().args.CONNECTION_OPTIONS_DATA_RETENTION_PERIOD * 24 * 60 * 60 * 1000
        # Delete the asset ids from CAR DB, assets which are not active based on retention period.
        self.delete_inactive_assets_associations(retention_timestamp)

        # Deleting the vertices
        for vertices, vertices_list in self.deleted_vertices.items():
            if vertices_list:
                context().car_service.delete(vertices, vertices_list)
        context().logger.info('Deleted vertices done: %s',
                              {key: len(value) for key, value in self.deleted_vertices.items()})
