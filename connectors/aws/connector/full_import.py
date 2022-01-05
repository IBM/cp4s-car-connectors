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

        # asset and network catalog
        collection = context().data_collector.create_asset(incremental=False)
        if collection:
            self.handle_data([
                'asset',
                'application',
                'asset_application',
                'ipaddress', 
                'hostname',
                'macaddress',
                'ipaddress_macaddress',
                'asset_ipaddress',
                'asset_hostname',
                'asset_macaddress',
                'geolocation',
                'asset_geolocation',
            ], collection)
            
        # database catalog
        collection_create, _ = context().data_collector.create_database(incremental=False) 
        if collection_create:
            self.handle_data([
                'database',
                'asset_database',
                'asset',
                'hostname',
                'asset_hostname',
                'asset_geolocation',
                'geolocation',
                'account',
                'account_database',
                'application',
                'user',
                'user_account',
                'asset_application',
            ], collection_create)

        # application catalog
        app_list, _ = context().data_collector.create_application(incremental=False)
        if app_list:
            self.handle_data([
                'application'
            ], app_list)

        # container catalog
        collection = context().data_collector.create_container(incremental=False)
        if collection:
            self.handle_data([
                'container',
                'ipaddress',
                'asset_container',
                'ipaddress_container',
            ], collection)

        # vulnerability catalog
        collection = context().data_collector.create_vulnerability(incremental=False)
        if collection:
            self.handle_data([
                'vulnerability',
                'asset_vulnerability',
            ], collection)


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

