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

    # Create source, report and source_report entry.
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

        # asset catalog
        collection = context().data_collector.create_asset(incremental=True)
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

        # network catalog
        interface_list, private_ipv4_host_update = context().data_collector.create_network()
        
        if interface_list:
            self.handle_data([
                'ipaddress',
                'hostname',
                'macaddress',
                'ipaddress_macaddress',
                'asset_ipaddress',
                'asset_hostname',
                'asset_macaddress',
            ], interface_list)

        if private_ipv4_host_update:
            self.handle_data([
                'ipaddress',
                'hostname',
                'ipaddress_macaddress',
                'asset_ipaddress',
                'asset_hostname',
            ], private_ipv4_host_update)

        # database catalog
        collection_create, collection_modify = context().data_collector.create_database(incremental=True) 

        if collection_modify:
            self.handle_data([
                'asset_database',
                'asset',
                'hostname',
                'asset_hostname',
                'asset_geolocation',
                'geolocation',
                'application',
                'asset_application',
            ], collection_modify)

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
        app_list, hosts_modify = context().data_collector.create_application(incremental=True)
        
        if hosts_modify:
            self.handle_data([
                'hostname',
                'asset_hostname',
            ], hosts_modify)

        if app_list:
            self.handle_data([
                'application'
            ], app_list)

        # container catalog
        collection = context().data_collector.create_container(incremental=True)
        if collection:
            self.handle_data([
                'container',
                'ipaddress',
                'asset_container',
                'ipaddress_container',
            ], collection)

        # vulnerability catalog
        collection = context().data_collector.create_vulnerability(incremental=True)
        if collection:
            self.handle_data([
                'vulnerability',
                'asset_vulnerability' ,
            ], collection)


        # Send collection data
        context().logger.info('Creating vertices')
        for name, data in self.data_handler.collections.items():
            self.send_data(name, data)
        context().logger.info('Creating vertices done: %s', {key: len(value) for key, value in self.data_handler.collections.items()})

        # update collection data
        context().data_collector.update_vertices()

    # Imports edges for all collection
    def import_edges(self):
        context().logger.info('Creating edges')
        for name, data in self.data_handler.edges.items():
            self.send_data(name, data)
        context().logger.info('Creating edges done: %s', {key: len(value) for key, value in self.data_handler.edges.items()})

        # update edges
        context().data_collector.update_edges()

    # Delete vertices that are deleted in data source
    def delete_vertices(self):
        context().data_collector.delete_vertices()

        self.data_handler.printData()

