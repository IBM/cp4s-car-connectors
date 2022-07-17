from car_framework.full_import import BaseFullImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping


class FullImport(BaseFullImport):
    """Full Import"""
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        # Get arguments from config
        self.config = context().asset_server.config

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    def import_collection(self):
        """
        Process the api response and creates initial import collections
        """
        context().logger.debug('Import collection started')
        collections = context().asset_server.get_asset_collections()
        for resource in endpoint_mapping:
            for node in endpoint_mapping[resource]:
                getattr(self.data_handler, 'handle_' + node.lower())(collections[resource])

    # Get save point from server
    def get_new_model_state_id(self):
        # If server doesn't have save point it can just return current time
        # So that it can be used for next incremental import
        return str(self.data_handler.timestamp)

    # Import all vertices from data source
    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()
