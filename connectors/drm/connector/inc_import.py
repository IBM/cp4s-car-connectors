from datetime import datetime, timedelta, timezone
from car_framework.inc_import import BaseIncrementalImport
from connector.data_handler import DataHandler, endpoint_mapping
from car_framework.context import context
from car_framework.util import IncrementalImportNotPossible


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        self.data_handler = DataHandler(None)

    def get_new_model_state_id(self):
        return context().drm_server.get_model_state_id()

    def create_source_report_object(self):
        return {'source': self.data_handler.source, 'report': self.data_handler.report,
                'source_report': self.data_handler.source_report}

    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        forceFullImport = context().args.forceFullImport
        if forceFullImport and forceFullImport.upper() == 'TRUE':
            raise IncrementalImportNotPossible("Specified force full import flag so skipping incremental import")
        self.last_model_state_id = last_model_state_id
        self.new_model_state_id = new_model_state_id

    # Import a collection; called by import_vertices
    def import_collection(self, drm_server_endpoint, car_resource_name):
        param = self.last_model_state_id
        collection = context().drm_server.get_collection(drm_server_endpoint, param)
        if collection != []:
            data = []
            if drm_server_endpoint == 'AssetRetention' or drm_server_endpoint == 'AssetUsage' or drm_server_endpoint == 'AssetDSList':
                self.update_vertices(collection, car_resource_name)
            for obj in collection:
                res = eval('self.data_handler.handle_%s(obj)' % drm_server_endpoint)
                if res:
                    data.append(res)
            if car_resource_name:
                self.send_data(car_resource_name, data)
            if drm_server_endpoint == 'AssetRetention' or drm_server_endpoint == 'AssetUsage' or drm_server_endpoint == 'AssetDSList':
                self.create_edge(obj, drm_server_endpoint)


    def create_edge(self, obj, drm_server_endpoint):
        lastupdate = (datetime.now() - timedelta(days=90)).replace(tzinfo=timezone.utc).timestamp()
        param = datetime.date(datetime.fromtimestamp(lastupdate)).strftime("%s")
        if drm_server_endpoint == 'AssetRetention' or drm_server_endpoint == 'AssetDSList':
            data = []
            edge_creation_endpoint = 'DSAPPLICATION'
            car_resource_name = 'application_ipaddress'
            new_edge_collection = context().drm_server.get_collection(edge_creation_endpoint, param)
            for item in new_edge_collection:
                if item['parentConceptId'] == str(obj['id']) or item['childConceptId'] == str(obj['id']):
                    res = eval('self.data_handler.handle_%s(item)' % edge_creation_endpoint)
                    if res:
                        data.append(res)
            self.send_data(car_resource_name, data)
        if drm_server_endpoint == 'AssetRetention' or drm_server_endpoint == 'AssetUsage':
            data = []
            edge_creation_endpoint = 'ApplicationBPMapping'
            car_resource_name = 'businessprocess_application'
            new_edge_collection = context().drm_server.get_collection(edge_creation_endpoint, param)
            for item in new_edge_collection:
                if item['parentId'] == str(obj['id']) or item['childConcept']['id'] == str(obj['id']):
                    res = eval('self.data_handler.handle_%s(item)' % edge_creation_endpoint)
                    if res:
                        data.append(res)
            self.send_data(car_resource_name, data)

    @staticmethod
    def update_vertices(collection, car_resource_name):
        deleted_id = []
        for obj in collection:
            deleted_id.append(str(obj['id']))
            context().car_service.delete(car_resource_name, deleted_id)

    # Import all vertices from data source
    def import_vertices(self):
        for drm_server_endpoint, car_resource_name in endpoint_mapping.items():
            self.import_collection(drm_server_endpoint, car_resource_name)

    # Imports edges for all collection
    def import_edges(self):
        for drm_server_endpoint, data_name in self.data_handler.edges.items():
            self.import_collection(drm_server_endpoint, data_name)

    # Imports deleted records for all collection
    def delete_collection(self, drm_server_endpoint, car_resource_name):
        param = self.last_model_state_id
        collection = context().drm_server.get_deleted_collection(drm_server_endpoint, param)
        data = []
        for obj in collection:
            res = eval('self.data_handler.handle_%s(obj)' % drm_server_endpoint)
            if res:
                data.append(res)
        if car_resource_name:
            self.send_data(car_resource_name, data)

    # Delete vertices that are deleted in data source
    def delete_vertices(self):
        for drm_server_endpoint, car_resource_name in endpoint_mapping.items():
            self.delete_collection(drm_server_endpoint, car_resource_name)
