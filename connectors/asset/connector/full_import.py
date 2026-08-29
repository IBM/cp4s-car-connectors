from car_framework.full_import import BaseFullImport
from connector.data_handler import DataHandler, endpoint_mapping
from car_framework.context import context


class FullImport(BaseFullImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        # If data source doesn't have external reference property None can be supplied as parameter.
        self.data_handler = DataHandler()

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Logic to import a collection; called by import_vertices
    def import_collection(self, asset_server_endpoint, name):
        collection = context().asset_server.get_collection(asset_server_endpoint)
        data = []
        for obj in collection:
            eval('self.data_handler.handle_%s(obj)' % asset_server_endpoint.lower())
            

    # GEt save point from server
    def get_new_model_state_id(self):
        # If server doesn't have save point it can just return current time
        # So that it can be used for next incremental import
        return context().asset_server.get_model_state_id()

    # Import all vertices from data source
    def import_vertices(self):
        self.data_handler.xrefproperties = context().asset_server.get_collection('xrefproperties')
        # can be left as it is if all the collection to be imported is lister in endpoint_mappingin data handler
        for asset_server_endpoint, data_name in endpoint_mapping.items():
            self.import_collection(asset_server_endpoint, data_name)

        self.data_handler.send_collections(self)

    # Imports edges for all collection
    def import_edges(self):
        # can be be left as it is if data handler manages the add edge logic
        self.data_handler.send_edges(self)
        self.data_handler.printData()
