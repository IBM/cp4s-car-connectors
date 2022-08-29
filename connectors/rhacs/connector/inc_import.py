from car_framework.inc_import import BaseIncrementalImport
from car_framework.context import context
from connector.data_handler import DataHandler
from requests.utils import quote


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        self.delta = {}
        self.last_model_state_id = ""
        self.assets_list = {}

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(context().report_time)


    # Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.last_model_state_id = float(last_model_state_id)
        self.delta, self.assets_list = context().asset_server.get_data_source(self.last_model_state_id)

    # Logic to import a collection between two save points; called by import_vertices
    def import_collection(self):
        """
        It will process the api response and does following operations
        Incremental create, Incremental update.
        """
        for node in ['cluster', 'node', 'application', 'container', 'account', 'user']:
            getattr(self.data_handler, 'handle_' + node.lower())(self.delta, self.last_model_state_id)

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
        update_edge = context().asset_server.get_deferred_vulnerability(self.last_model_state_id)
        for edge in update_edge:
            context().car_service.edge_patch(context().args.source, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(update_edge))

    def get_deleted_assets(self):
        """
        find the deleted assets from data source
        return: delete(dict) - Deleted list for each asset
        """

        container_delete = []
        ipaddress_delete = []
        asset_delete = []
        user_delete = []
        source = context().args.source

        # get vertices from car db
        asset = context().car_service.search_collection("asset", "source", source, ['external_id', 'asset_type'])
        ipaddress = context().car_service.search_collection("ipaddress", "source", source, ['external_id'])
        user = context().car_service.search_collection("user", "source", source, ['external_id'])

        # removed containers, clusters and node from data source
        for obj in asset['asset']:
            if obj['asset_type'] == 'container':
                if obj['external_id'] not in self.assets_list['container_list']:
                    container_delete.append(obj['external_id'])
            else:
                if obj['external_id'] not in self.assets_list['cluster_node_list'] and \
                        obj['external_id'] != 'central_stackrox_rhacs':
                    asset_delete.append(obj['external_id'])

        # removed ipaddress from data source
        for obj in ipaddress['ipaddress']:
            ip = obj['external_id'].replace('0/', '')
            if ip not in self.assets_list['ipaddress_list']:
                ipaddress_delete.append(ip)

        # removed user from data source
        for obj in user['user']:
            if obj['external_id'] not in self.assets_list['user_list']:
                user_delete.append(quote(obj['external_id']))

        delete = {'asset': asset_delete + container_delete,
                  'container': container_delete,
                  'ipaddress': ipaddress_delete,
                  'user': user_delete}

        return delete

    def delete_vertices(self):
        """
        Delete asset and containers
        Disable the inactive asset_vulnerability edges
        """
        # delete asset and disable vulnerability edges
        self.disable_edges()
        context().logger.info('Delete vertices started')
        delete = self.get_deleted_assets()
        for vertices, vertices_list in delete.items():
            if vertices_list:
                context().car_service.delete(vertices, vertices_list)
        context().logger.info('Deleting vertices done')
