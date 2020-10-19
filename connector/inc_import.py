from car_framework.inc_import import BaseIncrementalImport
from connector.data_handler import DataHandler, endpoint_mapping
from car_framework.context import context


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        # If data source doesn't have external reference property None can be supplied as parameter.
        self.data_handler = DataHandler(context().asset_server.get_collection('xrefproperties'))

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return context().asset_server.get_model_state_id()

    # Create source, report and source_report entry.
    def create_source_report_object(self):
        # Can be left as it is if they are populated in data handler constructor
        return {'source': self.data_handler.source, 'report': self.data_handler.report, 'source_report': self.data_handler.source_report}

    # Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.delta = context().asset_server.get_model_state_delta(last_model_state_id, new_model_state_id)

    # Add vertices for deletion
    def add_deletions(self, asset_server_endpoint, deletions):
        self.delta[asset_server_endpoint]['deletions'].extend(deletions)

    # Logic to import a collection between two save points; called by import_vertices
    def import_collection(self, asset_server_endpoint, car_resource_name):
        updates = self.delta.get(asset_server_endpoint) and self.delta.get(asset_server_endpoint).get('updates') or None
        if updates:
            collection = context().asset_server.get_objects(asset_server_endpoint, updates)
            data = []
            for obj in collection:
                updates.remove(obj['pk'])
                res = eval('self.data_handler.handle_%s(obj)' % asset_server_endpoint.lower())
                if res: data.append(res)
            if car_resource_name and data:
                self.send_data(car_resource_name, data)

            # If some resources cannot be loaded then they are deleted.
            self.add_deletions(asset_server_endpoint, updates)

    # Import all vertices from data source
    def import_vertices(self):
        # can be left as it is if all the collection to be imported is lister in endpoint_mappingin data handler
        for asset_server_endpoint, car_resource_name in endpoint_mapping.items():
            self.import_collection(asset_server_endpoint, car_resource_name)

    # Imports edges for all collection
    def import_edges(self):
        # can be be left as it is if data handler manages the add edge logic
        for name, data in self.data_handler.edges.items():
            self.send_data(name, data)

    # Delete vertices that are deleted in data source
    def delete_vertices(self):
        for asset_server_endpoint, car_resource_name in endpoint_mapping.items():
            deletions = self.delta.get(asset_server_endpoint) and self.delta.get(asset_server_endpoint).get('deletions') or None
            if deletions:
                context().car_service.delete(car_resource_name, deletions)
