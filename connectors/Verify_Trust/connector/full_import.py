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
                for handler in data_types:
                    getattr(self.data_handler, "handle_%s" % handler.lower())(collection)

    # Import all vertices from data source
    def import_vertices(self):

        # asset and host catalog
        collection = context().data_collector.create_user(incremental=False)
        if collection:
            self.handle_data([
                'user',
                'account',
                'user_account'
            ], collection)
            
        ip_address = context().data_collector.create_user(incremental=False)
        if ip_address:
            self.handle_data([
                'ipaddress',
                'account_ipaddress'
            ], ip_address)

        browser = context().data_collector.create_browser(incremental=False)
        if browser:
            self.handle_data([
                'browser',
                'browser_account',
                'browser_ipaddress'
            ], browser)
        # risk = context().data_collector.create_risk(incremental=False)
        # if risk:
        #     self.handle_data([
        #         'risk',
        #         'risk_ipaddress'
        #     ], risk)

        # # Send collection data
        self.data_handler.send_collections(self)

    # Imports edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()