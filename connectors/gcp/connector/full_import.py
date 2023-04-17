from car_framework.context import context
from car_framework.full_import import BaseFullImport
from connector.data_handler import DataHandler, deep_get


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
        """ Process the api response and creates initial import collections."""
        context().logger.debug('Import collection started')
        projects = context().asset_server.set_credentials_and_projects()
        for project, project_name in projects.items():
            # Handle VM instances
            vm_instances = context().asset_server.get_vm_instances(project)
            getattr(self.data_handler, 'handle_vm_instances')(vm_instances)

            vm_software_pkgs = context().asset_server.get_instances_pkgs(project)
            getattr(self.data_handler, 'handle_vm_software_pkgs')(vm_software_pkgs)

            vm_vulnerabilities = context().asset_server.get_instance_vulnerabilities(project)
            getattr(self.data_handler, 'handle_vm_vulnerabilities')(vm_vulnerabilities, project)
            # Handle app engine services
            web_apps = context().asset_server.get_web_applications(project)
            app_hostname = deep_get(web_apps[0], ['resource', 'data', 'defaultHostname'])
            web_app_services = context().asset_server.get_web_app_services(project)
            getattr(self.data_handler, 'handle_web_app_services')(web_app_services, web_apps)
            web_app_service_versions = context().asset_server.get_web_app_service_versions(project,)
            getattr(self.data_handler, 'handle_web_app_service_versions')(web_app_service_versions)
            web_service_names = [service['name'] for service in web_app_services]
            vulnerability = context().asset_server.get_scc_vulnerability(project)
            getattr(self.data_handler, 'handle_scc_vulnerability')(vulnerability, web_service_names,  app_hostname)

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
