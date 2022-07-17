from car_framework.full_import import BaseFullImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping, get_current_epoch_time


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

    # Get all asset and vulnerability records
    @staticmethod
    def get_active_host_vuln(ast_id, vuln_res):
        """
        Process the vulnerability response and filters active asset vulnerability
        parameters:
                active asset guid list, vulnerability response
        returns:
               List of active vulnerability
        """

        active_host_vuln = []
        for vuln in vuln_res:
            if vuln["status"] == "Active":
                vuln['machines'] = [ast for ast in vuln['machines'] if ast['guid'] in ast_id]
                active_host_vuln.append(vuln)
        return active_host_vuln

    def get_asset_vuln_records(self):
        """
        Process the api response and creates initial import collections
        parameters:
                   None
        returns:
                   List of hosts with vulnerability info
        """
        assets_res = context().asset_server.get_assets()
        assets_guid = []
        if assets_res:
            for asset in assets_res:
                assets_guid.append(asset.get("guid"))
        network_res = context().asset_server.network_interface(assets=assets_guid)
        # add network information(MAC) to the asset
        for asset in assets_res:
            mac_list = {}
            for key, value in network_res.items():
                machines = value["elementValues"]["ownerMachine"]["elementValues"]
                for machine in machines:
                    if asset["guid"] == machine["guid"]:
                        if value["simpleValues"].get("macAddressFormat") and \
                                value["simpleValues"]["macAddressFormat"]["values"]:
                            ipaddress_list = value["elementValues"]["ipAddress"]["elementValues"]
                            for ipaddress in ipaddress_list:
                                mac_list[ipaddress["name"]] = \
                                    value["simpleValues"]["macAddressFormat"]["values"]
            asset["mac_list"] = mac_list
        # Vulnerability information
        current_time = get_current_epoch_time()
        vulnerability_res = context().asset_server.get_vulnerabilities(
            current_model_state_id=current_time)
        active_vul_res = self.get_active_host_vuln(assets_guid, vulnerability_res)
        res_dict = {'asset': assets_res, 'vulnerability': active_vul_res}
        return res_dict

    # Logic to import a collection; called by import_vertices
    def import_collection(self):
        """
        Process the api response and creates initial import collections
        """
        context().logger.debug('Import collection started')
        collections = self. get_asset_vuln_records()
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
        # for asset_server_endpoint, data_name in endpoint_mapping.items():
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()
