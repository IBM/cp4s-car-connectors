from car_framework.full_import import BaseFullImport
from car_framework.context import context
from connector.data_handler import DataHandler

# This is to disable context().fooMember error in IDE
# pylint: disable=no-member 

class FullImport(BaseFullImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        # If data source doesn't have external reference property None can be supplied as parameter.
        self.data_handler = DataHandler()

    # Create source, report and source_report entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # GEt save point from server
    def get_new_model_state_id(self):
        # If server doesn't have save point it can just return current time
        # So that it can be used for next incremental import
        return str(self.data_handler.timestamp)

    # Logic to import collections or edges between two save points; called by import_vertices
    def handle_data(self, data_types, collection):
        if collection:
            for obj in collection:
                for handler in data_types:
                    getattr(self.data_handler, "handle_%s" % handler.lower())(obj)

    # Import all vertices from data source
    def import_vertices(self):

        self.create_asset_host()
        self.create_ipaddress_macaddress()
        self.create_vulnerability()
        self.create_application()
        self.create_database()

        # Send collection data
        context().logger.info('Creating vertices')
        for name, data in self.data_handler.collections.items():
            self.send_data(name, data)
        context().logger.info('Creating vertices: done %s', {key: len(value) for key, value in self.data_handler.collections.items()})

    # Imports edges for all collection
    def import_edges(self):
        context().logger.info('Creating edges')
        for name, data in self.data_handler.edges.items():
            self.send_data(name, data)
        context().logger.info('Creating edges done: %s', {key: len(value) for key, value in self.data_handler.edges.items()})
        
        self.data_handler.printData()


    def create_asset_host(self):
        collection = context().data_collector.create_asset_host(incremental=False)
        if collection:
            self.handle_data([
                'asset'
            ], collection)

    def create_ipaddress_macaddress(self):
        collection, _ = context().data_collector.create_ipaddress_macaddress(incremental=False)
        if collection:
            self.handle_data([
                'ipaddress',
                'hostname',
                'macaddress',
                'ipaddress_macaddress',
                'asset_ipaddress',
                'asset_hostname',
                'asset_macaddress',
            ], collection)

    def create_vulnerability(self):
        collection = context().data_collector.create_vulnerability(incremental=False)
        if collection:
            self.handle_data([
                'vulnerability',
                'asset_vulnerability',
            ], collection)

    def create_application(self):
        collection, _ = context().data_collector.create_application(incremental=False)
        if collection:
            self.handle_data([
                'asset',
                'hostname',
                'ipaddress',
                'application',
                'asset_application',
                'asset_hostname',
                'asset_ipaddress',
            ], collection)
        
    def create_database(self):
        collection, _, _ = context().data_collector.create_database(incremental=False)
        if collection:
            self.handle_data([
                'database',
                'asset_database',
                'asset',
                'hostname',
                'asset_hostname',
            ], collection)
