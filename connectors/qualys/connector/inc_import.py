from car_framework.context import context
from car_framework.inc_import import BaseIncrementalImport
from connector.data_handler import DataHandler, endpoint_mapping, get_epoch_time, find_location, deep_get


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

    # Imports edges for all collection
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
            for row in asset['HostAsset']['sourceInfo']['list']:
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
            if 'vmdrVulnList' in asset['HostAsset']:
                for vuln in asset['HostAsset']['vmdrVulnList']:
                    for app in asset['HostAsset']['applications']:
                        if app['productName'].lower() in vuln['RESULTS'].lower():
                            asset_edges['application'].discard(str(app['id']))
                    asset_edges['vulnerability'].discard(vuln['QID'])

            for edge_name, edge_ids in asset_edges.items():
                for edge_id in edge_ids:
                    self.update_edge.append({'from': asset_id, 'to': edge_id, 'edge_type': 'asset_'+edge_name})

    def get_active_asset_edges(self, asset_id):
        """
        Get active edges for an asset
        params: asset_id(str): asset id
        return: asset_edges(dict): active asset edges
        """

        asset_edges = {'ipaddress': set(), 'macaddress': set(), 'hostname': set(),
                       'account': set(), 'application': set(), 'vulnerability': set(), 'geolocation': set()}

        search_result = context().car_service.graph_search('asset', str(asset_id))

        if search_result['result'] and search_result['related']:

            for car_ip in search_result['related']:

                if 'ipaddress/' in str(deep_get(car_ip, ["node", "_id"])) and \
                        deep_get(car_ip, ["node", "_key"]) and \
                        context().args.source in deep_get(car_ip, ["link", "source"]):
                    asset_edges['ipaddress'].add(deep_get(car_ip, ["node", "_key"]))

                if 'macaddress/' in str(deep_get(car_ip, ["node", "_id"])) and \
                        deep_get(car_ip, ["node", "_key"]) and \
                        context().args.source in deep_get(car_ip, ["link", "source"]):
                    asset_edges['macaddress'].add(deep_get(car_ip, ["node", "_key"]))

                if 'account/' in str(deep_get(car_ip, ["node", "_id"])) and \
                        deep_get(car_ip, ["node", "external_id"]) and \
                        context().args.source in deep_get(car_ip, ["node", "source"]):
                    asset_edges['account'].add(deep_get(car_ip, ["node", "external_id"]))

                if 'vulnerability/' in str(deep_get(car_ip, ["node", "_id"])) and \
                        deep_get(car_ip, ["node", "disclosed_on"]) is None and \
                        context().args.source in deep_get(car_ip, ["node", "source"]):
                    asset_edges['vulnerability'].add(deep_get(car_ip, ["node", "external_id"]))

                if 'application/' in str(deep_get(car_ip, ["node", "_id"])) and \
                        context().args.source in deep_get(car_ip, ["node", "source"]):
                    asset_edges['application'].add(deep_get(car_ip, ["node", "external_id"]))

                if 'hostname/' in str(deep_get(car_ip, ["node", "_id"])) and \
                        context().args.source in deep_get(car_ip, ["node", "source"]):
                    asset_edges['hostname'].add(deep_get(car_ip, ["node", "_key"]))

                if 'geolocation/' in str(deep_get(car_ip, ["node", "_id"])) and \
                        context().args.source in deep_get(car_ip, ["node", "source"]):
                    asset_edges['geolocation'].add(deep_get(car_ip, ["node", "external_id"]))

        return asset_edges

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
