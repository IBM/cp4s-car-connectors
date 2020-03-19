import traceback
from enum import Enum
from base_import import BaseImport
from data_handler import DataHandler, endpoint_mapping


class Status(Enum):
    SUCCESS = 1
    FAILURE = 2
    INCREMENTAL_IMPORT_IS_NOT_POSSIBLE = 3


class IncrementalImport(BaseImport):
    def __init__(self, context):
        super().__init__(context)
        self.data_handler = DataHandler(context, self.context.asset_server.get_collection('xrefproperties'))


    def get_last_model_state_id(self):
        return self.context.car_service.get_last_model_state_id()


    def save_new_model_state_id(self, new_model_state_id):
        return self.context.car_service.save_new_model_state_id(new_model_state_id)


    def get_new_model_state_id(self):
        return self.context.asset_server.get_model_state_id()

    
    def create_source_report_object(self):
        return {'source': self.data_handler.source, 'report': self.data_handler.report, 'source_report': self.data_handler.source_report}


    def import_data(self, last_model_state_id, new_model_state_id):
        self.delta = self.context.asset_server.get_model_state_delta(last_model_state_id, new_model_state_id)
        self.import_vertices()
        self.wait_for_completion_of_import_jobs()
        self.import_edges()
        self.wait_for_completion_of_import_jobs()
        self.delete_vertices()

    
    def add_deletions(self, asset_server_endpoint, deletions):
        self.delta[asset_server_endpoint]['deletions'].extend(deletions)


    def import_collection(self, asset_server_endpoint, car_resource_name):
        updates = self.delta.get(asset_server_endpoint) and self.delta.get(asset_server_endpoint).get('updates') or None
        if updates:
            collection = self.context.asset_server.get_objects(asset_server_endpoint, updates)
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
                self.context.car_service.delete(car_resource_name, deletions)


    def run(self):
        try:
            last_model_state_id = self.get_last_model_state_id()
            last_model_state_id = '500'
            if not last_model_state_id:
                return Status.INCREMENTAL_IMPORT_IS_NOT_POSSIBLE

            new_model_state_id = self.get_new_model_state_id()
            if not new_model_state_id:
                return Status.INCREMENTAL_IMPORT_IS_NOT_POSSIBLE

            self.import_data(last_model_state_id, new_model_state_id)

            self.save_new_model_state_id(new_model_state_id)
            return Status.SUCCESS

        except Exception as e:
            traceback.print_exc()
            return Status.FAILURE
        