from car_framework.inc_import import BaseIncrementalImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping
from car_framework.util import IncrementalImportNotPossible


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        # self.data_handler = DataHandler()
        # self.create_source_report_object()
        # self.update_edge = []
        # self.delete_vulnerability = []
        # self.car_active_asset_edges = self.get_active_car_edges()

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.delta = context().asset_server.get_model_state_delta(last_model_state_id)
        self.last_model_state_id = last_model_state_id

    # Logic to import a collection between two save points; called by import_vertices
    def import_collection(self):
        """
        It will process the api response and does following operations
        Incremental create, Incremental update.
        returns:
            None
        """
        create_collections = self.incremental_create(self.delta)
        update_collections = self.incremental_update(self.delta)
        for collections in [create_collections, update_collections]:
            for resource in endpoint_mapping:
                for node in endpoint_mapping[resource]:
                    getattr(self.data_handler, 'handle_' + node.lower())(collections[resource])

    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        # can be left as it is if data handler manages the add edge logic
        self.data_handler.send_edges(self)

    def disable_edges(self):
        """ Disable the inactive edges """
        context().logger.info('Disabling edges')
        for edge in self.update_edge:
            context().car_service.edge_patch(context().args.source, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.update_edge))

    def delete_vertices(self):
        """
        It will in active the edges removed from data source
        """
        # disable asset and vulnerability edges
        self.disable_edges()
        context().logger.info('Delete vertices started')
        self.incremental_asset_delete()
        self.incremental_vulnerability_delete()
        context().logger.info('Deleting vertices done')

    def incremental_create(self, data):
        """
        It will fetch the incremental creation list
        returns:
            create_list(dict) : incremental asset and vulnerability list
        """
        # asset creation list
        creation_list = {}
        asset_list = []
        for asset in data['asset']:
            if float(asset["firstSeenTime"]) > float(self.last_model_state_id) and\
                    asset["status"] in ["Online", "Offline"]:
                asset_list.append(asset)
        creation_list["asset"] = asset_list

        # Vulnerability creation list
        vuln_list = []
        for vuln in data["vulnerability"]:
            if float(vuln["creationTime"]) > float(self.last_model_state_id) and vuln["status"] == "Active":
                vuln_list.append(vuln)
        creation_list["vulnerability"] = vuln_list
        return creation_list

    def incremental_update(self, data):
        """
        It will fetch the incremental update list
        returns:
            update_list(dict) : incremental updated asset and vulnerability list
        """
        updation_list = {"asset": self.incremental_asset_update(data),
                         "vulnerability": self.incremental_vuln_update(data)}
        return updation_list

    def incremental_asset_update(self, data):
        """
        It will fetch the incremental asset update list
        returns:
            asset_list(list) : incremental updated asset and list
        """
        asset_list = []
        for asset in data['asset']:
            disable_edges = {}
            asset_id = asset["guid"]
            if float(asset["firstSeenTime"]) < float(self.last_model_state_id) and \
                    asset["status"] in ["Online", "Offline"]:
                # handle hostname updates.
                disable_edges["asset_hostname"] = self.get_active_edge(asset_id, "asset_hostname")
                if asset.get("fqdn"):
                    for edge in disable_edges["asset_hostname"]:
                        if asset.get("fqdn") in edge["hostname_id"]:
                            disable_edges["asset_hostname"].remove(edge)
                            break
                elif asset.get("machineName"):
                    for edge in disable_edges["asset_hostname"]:
                        if asset.get("machineName").lower() in edge["hostname_id"]:
                            disable_edges["asset_hostname"].remove(edge)
                            break

                # Ip address, mac address handling
                disable_edges["asset_ipaddress"] = self.get_active_edge(asset_id, "asset_ipaddress")
                disable_edges["ipaddress_macaddress"] = self.get_active_edge(asset_id, "ipaddress_macaddress")
                for ipaddress in [asset.get("internalIpAddress"), asset.get("externalIpAddress")]:
                    for edge in disable_edges["asset_ipaddress"]:
                        if ipaddress in edge["ipaddress_id"]:
                            disable_edges["asset_ipaddress"].remove(edge)
                            break
                    for key, value in asset.get("mac_list").items():
                        if key == ipaddress:
                            for mac in value:
                                for mac_edge in disable_edges["ipaddress_macaddress"]:
                                    if mac in mac_edge["macaddress_id"]:
                                        disable_edges["ipaddress_macaddress"].remove(mac_edge)
                asset_list.append(asset)
                self.add_update_edges(disable_edges)
        return asset_list

    def incremental_vuln_update(self, data):
        """
        It will fetch the incremental vulnerability update list
        returns:
            asset_list(list) : incremental updated vulnerability list
        """
        vuln_list = []
        for vuln in data["vulnerability"]:
            if vuln["status"] == "Active":
                if float(vuln["creationTime"]) < float(self.last_model_state_id) and \
                        float(vuln["lastUpdateTime"]) > float(self.last_model_state_id):
                    disable_edges = {"asset_vulnerability": []}
                    active_vulnerability = self.get_active_malop_edges(vuln["guid"])
                    remediated_machines = self.get_remediated_machines(vuln["guid"])
                    # check for remediation status of the machine
                    for machine in remediated_machines:
                        for edge in active_vulnerability:
                            if machine in edge["asset_id"]:
                                disable_edges["asset_vulnerability"].append(edge)
                    # remove the machines which are not active:
                    active_machine = self.get_active_vertices("asset", ['external_id', 'name'])
                    inactive_assets = []
                    for machine in vuln["machines"]:
                        is_found = False
                        for asset in active_machine:
                            if asset["external_id"] == machine["guid"]:
                                is_found = True
                                break
                        if not is_found:
                            inactive_assets.append(machine)
                    for inactive_asset in inactive_assets:
                        vuln["machines"].remove(inactive_asset)
                    vuln_list.append(vuln)
                    self.add_update_edges(disable_edges)
        return vuln_list

    def get_active_vertices(self, resource, resource_fields):
        """
        It will fetch the active nodes from CAR Database
        returns:
            active_vertices(list) : list of active nodes
        """
        active_vertices = []
        result = context().car_service.search_collection(resource, 'source', context().args.source,
                                                                   resource_fields)
        if result:
            active_vertices = result[resource]
        return active_vertices

    def get_remediated_machines(self, malop_id):
        """
        It will fetch the remediation status of malop
        returns:
            remediated_machines(list) : list of remediated machines
        """
        remediation_logs = context().asset_server.get_malop_remediation_status(malop_id)
        remediated_machines = set()
        if remediation_logs:
            for log in remediation_logs:
                for machine in log["statusLog"]:
                    if machine["status"] == "SUCCESS":
                        remediated_machines.add(machine["machineId"])
        return remediated_machines

    def get_active_malop_edges(self, vuln_id):
        """
        It will fetch the active asset_vulnerability edges from all edges
        returns:
            malop_edges(list) : list of asset_vulnerability edges
        """
        malop_edges = []
        for edge in self.car_active_asset_edges["asset_vulnerability"]:
            if vuln_id in edge["vulnerability_id"]:
                malop_edges.append(edge)
        return malop_edges

    def get_active_edge(self, asset_id, edge_type):
        """
        It will fetch the active asset edges from all active edges
        returns:
            edges(list) : list of active edges
        """
        edges = []
        if "asset" in edge_type:
            for edge in self.car_active_asset_edges[edge_type]:
                if asset_id in edge["asset_id"]:
                    edges.append(edge)
        else:
            asset_edge = "asset_" + edge_type.split('_')[0]
            for edge in self.car_active_asset_edges[asset_edge]:
                if asset_id in edge["asset_id"]:
                    to_id = edge_type.split('_')[0] + "_id"
                    search_id = edge[to_id]
                    for key in self.car_active_asset_edges[edge_type]:
                        if search_id in key[to_id]:
                            edges.append(key)
        return edges

    def get_active_car_edges(self):
        """
        It will fetch the active edges from CAR Database
        returns:
            car_active_asset_edges(dict) : dict of edges
        """
        car_active_asset_edges = {}
        source = context().args.source
        edges = ["asset_ipaddress", "ipaddress_macaddress",
                 "asset_hostname", "asset_vulnerability"]
        for edge in edges:
            car_active_asset_edges[edge] = []
            edge_from, edge_to = edge.split("_")
            from_id = edge_from + "_id"
            to_id = edge_to + "_id"
            edge_fields = [from_id, to_id, 'source']
            result = context().car_service.search_collection(edge, "source", source, edge_fields)
            if result:
                car_active_asset_edges[edge] = result[edge]
        return car_active_asset_edges

    def add_update_edges(self, edges):
        """
        Add all edges to be disabled
        """
        for edge_type, values in edges.items():
            for value in values:
                from_resource, to_resource = edge_type.split('_')
                from_id = value[from_resource + '_id'].split('/', 1)[1]
                to_id = value[to_resource + '_id'].split('/', 1)[1]
                self.update_edge.append({'from': from_id, 'to': to_id, 'edge_type': edge_type})

    def incremental_asset_delete(self):
        """
        Delete asset nodes from CAR Database if status changed to stale or archive
        """
        asset_delete = []
        stale_or_archive_assets = context().asset_server.get_assets(incremental_delete=True)
        active_car_assets = self.get_active_vertices("asset", ['external_id', 'name'])
        if stale_or_archive_assets:
            for asset in stale_or_archive_assets:
                for active_asset in active_car_assets:
                    if asset["guid"] == active_asset["external_id"]:
                        asset_delete.append(asset["guid"])
        if asset_delete:
            context().car_service.delete("asset", asset_delete)
        context().logger.info('Deleting vertices done: %s', {'asset': len(asset_delete)})

    def incremental_vulnerability_delete(self):
        """
        Delete closed or remediated vulnerabilities
        """
        vulnerability_delete = []
        if self.delta["vulnerability"]:
            for vuln in self.delta["vulnerability"]:
                if vuln["status"] != "Active":
                    vulnerability_delete.append(vuln["guid"])
        self.delete_vulnerability = vulnerability_delete
        if vulnerability_delete:
            context().car_service.delete("vulnerability", vulnerability_delete)
        context().logger.info('Deleting vertices done: %s', {'vulnerability': len(vulnerability_delete)})

    # To disbale incremental import
    def run(self):
        raise IncrementalImportNotPossible('Connector doesn\'t support incremental import.')