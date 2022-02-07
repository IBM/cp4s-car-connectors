from car_framework.inc_import import BaseIncrementalImport
from car_framework.context import context
from connector.data_handler import DataHandler

# This is to disable context().fooMember error in IDE
# pylint: disable=no-member

class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        # If data source doesn't have external reference property None can be supplied as parameter.
        self.data_handler = DataHandler()
        self.create_source_report_object()

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source and report entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Save last and new save points to gather data from 
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        context().new_model_state_id = new_model_state_id
        context().last_model_state_id = last_model_state_id

    # Logic to import collections or edges between two save points; called by import_vertices
    def handle_data(self, data_types, collection):
        if collection:
            for obj in collection:
                for handler in data_types:
                    getattr(self.data_handler, "handle_%s" % handler.lower())(obj)

    # Import all vertices from data source
    def import_vertices(self):

        # it should go in context().data_collector.update_vertices ?
        context().data_collector.vulnerability_patch()
        
        self.create_asset_host()
        self.create_ipaddress_macaddress()
        self.create_vulnerability()
        self.create_application()
        self.create_database()

        self.update_hostname_vm()
        self.update_hostname_app()

        # Send collection data
        context().logger.info('Creating vertices')
        for name, data in self.data_handler.collections.items():
            self.send_data(name, data)
        context().logger.info('Creating vertices done: %s', {key: len(value) for key, value in self.data_handler.collections.items()})

    # Imports edges for all collection
    def import_edges(self):
        context().logger.info('Creating edges')
        for name, data in self.data_handler.edges.items():
            self.send_data(name, data)
        context().logger.info('Creating edges done: %s', {key: len(value) for key, value in self.data_handler.edges.items()})

        # update edges
        context().data_collector.update_edges()

    def create_asset_host(self):
        collection = context().data_collector.create_asset_host(incremental=True)
        if collection:
            self.handle_data([
                'asset'
            ], collection)

    def create_ipaddress_macaddress(self):
        _, collection = context().data_collector.create_ipaddress_macaddress(incremental=True)
        if collection:
            self.handle_data([
                'ipaddress',
                'asset_ipaddress',
                'ipaddress_macaddress',
            ], collection)

    def create_vulnerability(self):
        collection = context().data_collector.create_vulnerability(incremental=True)
        if collection:
            self.handle_data([
                'vulnerability',
                'asset_vulnerability',
            ], collection)

    def create_application(self):
        application_list, update_ip = context().data_collector.create_application(incremental=True)
        if application_list:
            self.handle_data([
                'asset',
                'hostname',
                'ipaddress',
                'application',
                'asset_application',
                'asset_hostname',
                'asset_ipaddress',
            ], application_list)

        if update_ip:
            self.handle_data([
                'ipaddress',
                'asset_ipaddress',
            ], update_ip)

    def update_hostname_vm(self):
        collection = context().data_collector.update_hostname_vm(incremental=True)
        if collection:
            self.handle_data([
                'hostname',
                'asset_hostname',
            ], collection)

    def update_hostname_app(self):
        collection = context().data_collector.update_hostname_app(incremental=True)
        if collection:
            self.handle_data([
                'hostname',
                'asset_hostname',
            ], collection)
        
    def create_database(self):
        initial_db_list, server_list, database_list= context().data_collector.create_database(incremental=True)
        if initial_db_list:
            self.handle_data([
                'database',
                'asset_database',
                'asset',
                'hostname',
                'asset_hostname',
            ], initial_db_list)

        if server_list:
            self.handle_data([
                'asset',
                'hostname',
                'asset_hostname',
            ], server_list)

        if database_list:
            self.handle_data([
                'database',
                'asset_database',
            ], database_list)

    # Delete vertices that are deleted in data source
    def delete_vertices(self):
        context().data_collector.delete_vertices()

        self.data_handler.printData()

