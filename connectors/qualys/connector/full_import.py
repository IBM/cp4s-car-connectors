from connector.data_handler import DataHandler, endpoint_mapping, append_vuln_in_asset
from car_framework.full_import import BaseFullImport
from car_framework.context import context


class FullImport(BaseFullImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        # Get arguments from config
        self.config = context().asset_server.config

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Get all asset and vulnerability records
    def get_host_vuln_records(self):
        """
        Process the api response and creates initial import collections
        parameters:
                   None
        returns:
                   List of hosts with vulnerability info
               """
        host_list = context().asset_server.get_assets()
        vulnerability_list = context().asset_server.get_vulnerabilities()
        applications = context().asset_server.get_applications()
        return append_vuln_in_asset(host_list, vulnerability_list, applications)

    # Logic to import a collection; called by import_vertices
    def import_collection(self):
        """
        Process the api response and creates initial import collections
        parameters:
            None
        returns:
            None
        """
        context().logger.debug('Import collection started')
        collections = self. get_host_vuln_records()
        resources = endpoint_mapping['asset'] + endpoint_mapping['vulnerability']
        if collections:
            for collection in collections:
                for node in resources:
                    getattr(self.data_handler, 'handle_' + node.lower())(collection)

    # Get save point from server
    def get_new_model_state_id(self):
        # If server doesn't have save point it can just return current time
        # So that it can be used for next incremental import
        return str(self.data_handler.timestamp)

    # Import all vertices from data source
    def import_vertices(self):
        context().logger.debug('Import vertices started')
        # for asset_server_endpoint, data_name in endpoint_mapping.items():
        self.import_collection()
        self.data_handler.send_collections(self)

    # Imports edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()
