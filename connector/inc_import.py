from car_framework.inc_import import BaseIncrementalImport
from data_handler import DataHandler, endpoint_mapping
from car_framework.context import context


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        self.data_handler = DataHandler(context().asset_server.get_collection('xrefproperties'))


    def get_new_model_state_id(self):
        return context().asset_server.get_model_state_id()

    
    def create_source_report_object(self):
        return {'source': self.data_handler.source, 'report': self.data_handler.report, 'source_report': self.data_handler.source_report}


    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.delta = context().asset_server.get_model_state_delta(last_model_state_id, new_model_state_id)


    def add_deletions(self, asset_server_endpoint, deletions):
        self.delta[asset_server_endpoint]['deletions'].extend(deletions)


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


    def import_vertices(self):
        for asset_server_endpoint, car_resource_name in endpoint_mapping.items():
            self.import_collection(asset_server_endpoint, car_resource_name)


    def import_edges(self):
        for name, data in self.data_handler.edges.items():
            self.send_data(name, data)


    def delete_vertices(self):
        for asset_server_endpoint, car_resource_name in endpoint_mapping.items():
            deletions = self.delta.get(asset_server_endpoint) and self.delta.get(asset_server_endpoint).get('deletions') or None
            if deletions:
                context().car_service.delete(car_resource_name, deletions)
