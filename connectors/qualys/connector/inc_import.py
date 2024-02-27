import json
from car_framework.context import context
from car_framework.inc_import import BaseIncrementalImport
from connector.data_handler import DataHandler, endpoint_mapping, get_epoch_time, find_location, deep_get,\
    update_vuln_node_with_kb

class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        self.create_source_report_object()
        self.update_edge = []

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.delta = context().asset_server.get_model_state_delta(last_model_state_id, new_model_state_id)
        self.last_model_state_id = last_model_state_id

    def import_collection(self):
        """
        It will process the api response and does following operations
        Incremental create, Incremental update.
        returns:
            None
        """
        # Update vulnerability nodes if update_vulnerability flag enabled
        if context().args.update_existing_vulnerability_cve:
            self.update_existing_vulnerability_cve()

        resources = endpoint_mapping['asset'] + endpoint_mapping['vulnerability']

        # process the recent records from data source
        for collection in self.delta:
            for node in resources:
                getattr(self.data_handler, 'handle_' + node.lower())(collection)

    # Import all vertices from data source
    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)

    def compute_inactive_edges(self, asset):
        """
        Finds the inactive edges by comparing active asset edges
        from CAR DB and data source asset information
        params: asset(str): host asset response
        """

        context().logger.debug('Update vertices started')

        asset_id = asset['HostAsset']['id']

        # Ignore the newly created assets
        if float(self.last_model_state_id) > get_epoch_time(asset['HostAsset']['created']):

            asset_edges = self.get_active_asset_edges(asset_id)

            if asset['HostAsset'].get('dnsHostName'):
                asset_edges['hostname'].discard(asset['HostAsset'].get('dnsHostName').lower())
            elif asset['HostAsset'].get('name'):
                asset_edges['hostname'].discard(asset['HostAsset']['name'].lower())

            # remove active account from edge list
            if asset['HostAsset'].get('account'):
                for account in asset['HostAsset']['account']['list']:
                    asset_edges['account'].discard(account['HostAssetAccount']['username'])

            # remove active geo location from edge list
            for row in deep_get(asset, ['HostAsset', 'sourceInfo', 'list'], []):
                for asset_location in row:
                    asset_edges['geolocation'].discard(find_location(row[asset_location]))

            # remove active ipaddress, macaddress from edge list
            network_interface = asset['HostAsset'].get('networkInterface', {})
            for interface in network_interface.get('list', {}):
                asset_edges['ipaddress'].discard(interface['HostAssetInterface']['address'])
                key = interface['HostAssetInterface'].get('macAddress', "")
                if not key:
                    continue
                asset_edges['macaddress'].discard(key)

            # remove active vulnerability, application from edge list
            if 'vmdrVulnList' in asset['HostAsset'] and 'applications' in asset['HostAsset']:
                for vuln in asset['HostAsset']['vmdrVulnList']:
                    for app in asset['HostAsset']['applications']:
                        if app['productName'].lower() in vuln['RESULTS'].lower():
                            asset_edges['application'].discard(str(app['id']))
                    asset_edges['vulnerability'].discard(vuln['QID'])

            for edge_name, edge_ids in asset_edges.items():
                for edge_id in edge_ids:
                    self.update_edge.append({'from': asset_id, 'to': edge_id, 'edge_type': 'asset_' + edge_name})

    def get_active_asset_edges(self, asset_id):
        """
        Get active edges for an asset
        params: asset_id(str): asset id
        return: asset_edges(dict): active asset edges
        """

        asset_edges = {'ipaddress': set(), 'macaddress': set(), 'hostname': set(),
                       'account': set(), 'application': set(), 'vulnerability': set(), 'geolocation': set()}

        for key in asset_edges.keys():
            edge_type = "asset_" + key
            asset_edge_id = context().args.source + '/' + str(asset_id)
            edges = self.query_active_edges(edge_type, asset_edge_id, key)
            to_field = key + "_id"
            if "data" in edges:
                for edge in edges["data"][edge_type]:
                    asset_edges[key].add(edge[to_field].split('/', 1)[1])
        return asset_edges

    def query_active_edges(self, edge_type, asset_id, resource_name):
        """
        Query CARDB for list of asset related edges
        params: edge_type(str) : type of the edge
                asset_id(str): asset_id values in edge
                resource_name: resource name
        """
        # GraphQL uses api version v3.
        api_version = '/api/car/v3'
        # Graph query
        data = "{\"query\":\"query { %s(where: {asset_id: {_eq: \\\"%s\\\"}}) " \
               "{  source, asset_id, %s_id  }}\"}" % (edge_type, asset_id, resource_name)

        search_result = context().car_service.communicator.post('query', data=data,
                                                                api_version=api_version)
        return json.loads(search_result.content)

    def disable_edges(self):
        """ Disable the inactive edges """
        context().logger.info('Disabling edges')
        for edge in self.update_edge:
            context().car_service.edge_patch(context().args.source, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.update_edge))

    # Delete vertices that are deleted in data source
    def delete_vertices(self):
        """
        It will in active the edges removed from data source
        """
        for asset in self.delta:
            self.compute_inactive_edges(asset)
        self.disable_edges()
        context().logger.info('Delete vertices started')

    def update_existing_vulnerability_cve(self):
        """
        Update existing vulnerabilities with knowledgebase details
        """
        # Get vulnerability nodes from CAR DB
        vuln_nodes = context().car_service.search_collection('vulnerability', 'source', context().args.source,
                                                         ['external_id', 'name', 'base_score', 'description'])
        # Get vulnerability ids from nodes
        vuln_ids = [vuln_id['external_id'] for vuln_id in vuln_nodes['vulnerability']]

        # Vulnerability knowledgebase details
        if vuln_ids:
            vuln_kb = context().asset_server.get_knowledge_base_vuln_list(vuln_ids)
            vuln_kb = {vuln['QID']: vuln for vuln in vuln_kb}
            for node in vuln_nodes['vulnerability']:
                kb = vuln_kb[node['external_id']]
                update_vuln_node_with_kb(node, kb)
                self.data_handler.add_collection('vulnerability', node, 'external_id')
        self.data_handler.send_collections(self)
        # Reset the collections once updated vulnerability nodes are imported to CAR DB
        self.data_handler.collections = {}
        self.data_handler.collection_keys = {}
