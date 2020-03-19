from full_import import FullImport
from data_handler import DataHandler, endpoint_mapping


class ExampleFullImport(FullImport):
    def __init__(self, context):
        super().__init__(context)
        self.data_handler = DataHandler(context, self.context.asset_server.get_collection('xrefproperties'))


    def create_source_report_object(self):
        return {'source': self.data_handler.source, 'report': self.data_handler.report, 'source_report': self.data_handler.source_report}


    def import_collection(self, asset_server_endpoint, name):
        collection = self.context.asset_server.get_collection(asset_server_endpoint)
        data = []
        for obj in collection:
            res = eval('self.data_handler.handle_%s(obj)' % asset_server_endpoint.lower())
            if res: data.append(res)
        if name:
            self.send_data(name, data)


    def get_new_model_state_id(self):
        return self.context.asset_server.get_model_state_id()


    def save_new_model_state_id(self, new_model_state_id):
        return self.context.car_service.save_new_model_state_id(new_model_state_id)


    def import_vertices(self):
        for asset_server_endpoint, data_name in endpoint_mapping.items():
            self.import_collection(asset_server_endpoint, data_name)


    def import_edges(self):
        for name, data in self.data_handler.edges.items():
            self.send_data(name, data)
