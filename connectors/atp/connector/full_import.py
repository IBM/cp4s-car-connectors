from car_framework.full_import import BaseFullImport
from car_framework.context import context
from connector.data_handler import DataHandler

class FullImport(BaseFullImport):
    def __init__(self):
        # initialize the data handler.
        # If data source doesn't have external reference property None can be supplied as parameter.
        self.data_handler = DataHandler()
        super().__init__()

    # Create source and report entry.
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

        # asset and host catalog
        collection = context().data_collector.create_asset_host(incremental=False)
        print(collection)
        if collection:
            self.handle_data([
                'asset',
                'hostname',
                'asset_hostname',
                'application',
                'asset_application',
            ], collection)
            
        # ip address and mac address catalog
        network_list, _, _, _ = context().data_collector.create_ipaddress_macaddress(incremental=False) 
        if network_list:
            self.handle_data([
                'ipaddress',
                'macaddress',
                'ipaddress_macaddress',
                'asset_ipaddress',
                'asset_macaddress',
                'asset',
                'hostname',
                'asset_hostname',
                'application',
                'asset_application',
            ], network_list)

        # user catalog
        user_list = context().data_collector.create_user(incremental=False)
        if user_list:
            self.handle_data([
                'user',
                'asset_account',
                'account_hostname',
                'account',
                'user_account',
                'unifiedaccount',
                'account_unifiedaccount'
            ], user_list)

        # vulnerability catalog
        # vuln_list, application_create, vulnerability_update, app_vuln_edge, vulnerability_create = context().data_collector.create_vulnerability(incremental=False)
        vuln_list, _, _, _, _ = context().data_collector.create_vulnerability(incremental=False)
        if vuln_list:
            self.handle_data([
                'application',
                'asset_application',
                'vulnerability',
                'asset_vulnerability'
            ], vuln_list)

        # Send collection data
        self.data_handler.send_collections(self)

    # Imports edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()