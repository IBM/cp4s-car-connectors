from car_framework.context import context
from car_framework.full_import import BaseFullImport
from connector.data_handler import DataHandler, update_app_with_cpe


class FullImport(BaseFullImport):
    """Full Import"""

    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Logic to import a collection; called by import_vertices
    def import_collection(self):
        """ Process the api response and creates initial import collections"""
        context().logger.debug('Import collection started')
        assets = context().asset_server.get_query_results(category='asset')
        sensors = context().asset_server.get_query_results(category='sensor')
        sensors = {value['host']: value for value in sensors}
        getattr(self.data_handler, 'handle_nozomi_assets')(assets, sensors)
        nodes = context().asset_server.get_query_results(category='node')
        getattr(self.data_handler, 'handle_nozomi_nodes')(nodes)
        # Software list provide application cpe and asset_softwares provide applications on the asset
        # Using both responses, updating asset_softwares with cpe details.
        software_list = context().asset_server.get_query_results(category='software_list')
        applications = context().asset_server.get_query_results(category='asset_softwares')
        update_app_with_cpe(applications, software_list)
        getattr(self.data_handler, 'handle_nozomi_applications')(applications)
        vulnerabilities = context().asset_server.get_query_results(category='asset_cve',
                                                                   query_filter=f'where resolved=="false"')
        getattr(self.data_handler, 'handle_nozomi_vulnerabilities')(vulnerabilities)
        getattr(self.data_handler, 'handle_nozomi_app_vuln')(applications, vulnerabilities)

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
