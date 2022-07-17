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

        user_collection = context().data_collector.create_user(incremental=False)
        if user_collection:
            self.handle_data([
                'user',
                'account',
                'user_account'
            ], user_collection)

        group_collection = context().data_collector.create_group(incremental=False)
        if group_collection:
            self.handle_data([
                'group'
            ], group_collection)

        # manager_collection = context().data_collector.create_managers(incremental=False)
        # if group_collection:
        #     self.handle_data([
        #         'account_account'
        #     ], group_collection)

        user_group_list = context().data_collector.create_account_group(incremental=False)
        if user_group_list:
            self.handle_data([
                'account_group'
            ], user_group_list)

        app_role_list = context().data_collector.create_approle(incremental=False)
        if app_role_list:
            self.handle_data([
                'approle',
                'account_approle',
                'group_approle'
            ], app_role_list)

        permissions_list = context().data_collector.create_permissions(incremental=False)
        if permissions_list:
            self.handle_data([
                'permissiongrants',
                'group_permissiongrants'
            ], permissions_list)

        signins_audit_logs = context().data_collector.create_signins(incremental=False)
        if signins_audit_logs:
            self.handle_data([
                'application',
                'ipaddress',
                'asset',
                'browser',
                'signin',
                'geolocation',
                'approle_from_signin',
                'account_from_signin',
                'account_application',
                'account_ipaddress',
                'account_signin',
                'asset_account',
                'browser_account',
                'asset_application',
                'application_ipaddress',
                'asset_geolocation',
                'signin_application',
                'signin_approle',
                'signin_asset',
                'signin_geolocation',
                'signin_ipaddress'
            ], signins_audit_logs)

        audit_logs = context().data_collector.create_audits(incremental=False)
        if audit_logs:
            self.handle_data([
                'audit',
                'account_from_audits',
                'group_from_audits',
                'application_from_audits',
                'ipaddress',
                'audit_account',
                'audit_group',
                'audit_application',
                'account_ipaddress',

            ], audit_logs)
        
        # Send collection data
        self.data_handler.send_collections(self)

    # Imports edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()