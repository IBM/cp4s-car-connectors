from car_framework.inc_import import BaseIncrementalImport
from car_framework.context import context
from connector.data_handler import DataHandler


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        # initialize the data handler.
        # If data source doesn't have external reference property None can be supplied as parameter.
        self.data_handler = DataHandler()
        super().__init__()
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

        # asset and host catalog
        collection = context().data_collector.create_asset_host(incremental=True)
        if collection:
            self.handle_data([
                'asset',
                'hostname',
                'asset_hostname',
                'application',
                'asset_application',
            ], collection)
            
        # ip address and mac address catalog
        network_list, ip_data, mac_data, ip_mac = context().data_collector.create_ipaddress_macaddress(incremental=True) 
        if network_list:
            self.handle_data([
                'asset',
                'hostname',
                'asset_hostname',
                'application',
                'asset_application',
                'ipaddress',
                'macaddress',
                'ipaddress_macaddress',
                'asset_ipaddress',
                'asset_macaddress',
            ], network_list)
        
        if ip_data:
            self.handle_data([
                'ipaddress',
                'asset_ipaddress',
            ], ip_data)
        
        if mac_data:
            self.handle_data([
                'macaddress',
                'asset_macaddress',
            ], mac_data)
        
        if ip_mac:
            self.handle_data([
                'ipaddress_macaddress',
            ], ip_mac)

        # user catalog
        user_list = context().data_collector.create_user(incremental=True)
        if user_list:
            self.handle_data([
                'user',
                'asset_account',
                'account_hostname',
                'account',
                'user_account',
            ], user_list)

        # vulnerability catalog
        vuln_list, application_create, vulnerability_update, app_vuln_edge, vulnerability_create = context().data_collector.create_vulnerability(incremental=True)
        if vuln_list:
            self.handle_data([
                'application',
                'asset_application',
                'vulnerability',
                'asset_vulnerability',
                'application_vulnerability'
            ], vuln_list)

        if application_create:
            self.handle_data([
                'application',
                'asset_application',
                'application_vulnerability'
            ], application_create)
            
        if vulnerability_update:
            self.handle_data([
                'vulnerability',
                'asset_vulnerability',
                'application_vulnerability'
            ], vulnerability_update)
            
        if app_vuln_edge:
            self.handle_data([
                'application_vulnerability'
            ], app_vuln_edge)
            
        if vulnerability_create:
            self.handle_data([
                'application',
                'asset_application',
                'application_vulnerability',
                'vulnerability',
                'asset_vulnerability',
            ], vulnerability_create)

        # Send collection data
        self.data_handler.send_collections(self)

    # Imports edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)

        # update edges
        context().data_collector.update_edges()

    # Delete vertices that are deleted in data source
    def delete_vertices(self):
        context().data_collector.delete_vertices()

        self.data_handler.printData()