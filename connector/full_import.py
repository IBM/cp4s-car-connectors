from car_framework.full_import import BaseFullImport
from data_handler import DataHandler, endpoint_mapping
from car_framework.context import context


class FullImport(BaseFullImport):
    def __init__(self):
        super().__init__()
        self.data_handler = DataHandler(context().asset_server.get_collection('xrefproperties'))


    def create_source_report_object(self):
        return {'source': self.data_handler.source, 'report': self.data_handler.report, 'source_report': self.data_handler.source_report}


    def import_collection(self, asset_server_endpoint, name):
        collection = context().asset_server.get_collection(asset_server_endpoint)
        data = []
        for obj in collection:
            res = eval('self.data_handler.handle_%s(obj)' % asset_server_endpoint.lower())
            if res: data.append(res)
        if name:
            self.send_data(name, data)


    def get_new_model_state_id(self):
        return context().asset_server.get_model_state_id()


    def import_vertices(self):
        for asset_server_endpoint, data_name in endpoint_mapping.items():
            self.import_collection(asset_server_endpoint, data_name)


    def import_edges(self):
        for name, data in self.data_handler.edges.items():
            self.send_data(name, data)
