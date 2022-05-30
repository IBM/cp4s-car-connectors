from car_framework.full_import import BaseFullImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping


class FullImport(BaseFullImport):
    """Full Import"""
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        # Get arguments from config
        self.config = context().asset_server.config

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    def get_asset_vuln_records(self):
        """
        Process the api response and creates initial import collections
        parameters:
            None
        returns:
            List of hosts with vulnerability info
        """
        assets_res = context().asset_server.get_assets()
        application_res = context().asset_server.get_application()
        context().asset_server.get_applications_users(application_res)
        system_log = context().asset_server.get_systemlogs()
        # user log-in failures are considered vulnerabilities.
        # if user log-in successful later considered as vulnerability resolution,
        # edge will be disabled between asset and vulnerability
        vulnerability_res = self.get_user_login_failures(assets_res, system_log)
        res_dict = {'asset': assets_res, 'application': application_res, 'vulnerability': vulnerability_res}
        return res_dict

    def get_user_login_failures(self, assets, logs):
        """
        Process the api response and creates initial import collections
        parameters:
            assets(list): list of users
            logs(list): list of user log-in events
        returns:
            List of log-in failure event logs
        """
        user_list = [x["id"] for x in assets]
        login_failures = list()
        for log in logs:
            if log["outcome"]["result"] != "SUCCESS" and log["actor"]["id"] in user_list:
                is_present = False
                # if subsequent log-in attempts are failed increment risk score by 1
                for login_failure in login_failures:
                    if log["actor"]["id"] == login_failure["actor"]["id"]:
                        login_failure['score'] += 1
                        is_present = True
                        break
                if not is_present:
                    log['score'] = 1
                    login_failures.append(log)
            elif log["outcome"]["result"] == "SUCCESS":
                # Remove entry if the subsequent log-in attempt successful
                for login_failure in login_failures:
                    if log["actor"]["id"] == login_failure["actor"]["id"]:
                        login_failures.remove(login_failure)
                        break
        return login_failures

    # Logic to import a collection; called by import_vertices
    def import_collection(self):
        """
        Process the api response and creates initial import collections
        """
        context().logger.debug('Import collection started')
        collections = self.get_asset_vuln_records()
        for resource in endpoint_mapping:
            for node in endpoint_mapping[resource]:
                getattr(self.data_handler, 'handle_' + node.lower())(collections[resource])

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
