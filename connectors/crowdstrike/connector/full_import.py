from car_framework.context import context
from car_framework.full_import import BaseFullImport
from connector.data_handler import DataHandler, deep_get, group_host_sensor_apps


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
        hosts = context().asset_server.get_hosts()
        agent_related_asset_ids = {host['aid']: host['id'] for host in hosts if deep_get(host, ['aid'])}
        getattr(self.data_handler, 'handle_asset')(hosts)
        applications = context().asset_server.get_applications()
        getattr(self.data_handler, 'handle_application')(applications)
        accounts = context().asset_server.get_accounts()
        account_logins = context().asset_server.get_logins(accounts)
        getattr(self.data_handler, 'handle_account')(account_logins)
        vulnerabilities = context().asset_server.get_vulnerabilities()
        agent_applications_map = group_host_sensor_apps(applications)
        context().asset_server.get_vulnerable_applications(vulnerabilities, agent_applications_map)
        getattr(self.data_handler, 'handle_vulnerability')(vulnerabilities, agent_related_asset_ids)

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
