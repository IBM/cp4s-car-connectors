from datetime import datetime, timedelta, timezone
from car_framework.full_import import BaseFullImport
from connector.data_handler import DataHandler, endpoint_mapping
from car_framework.context import context


class FullImport(BaseFullImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler(None)

    # Create source, report and source_report entry.
    def create_source_report_object(self):
        return {'source': self.data_handler.source, 'report': self.data_handler.report,
                'source_report': self.data_handler.source_report}

    #  Import a collection; called by import_vertices
    def import_collection(self, drm_server_endpoint, name):
        lastupdate = (datetime.now() - timedelta(days=90)).replace(tzinfo=timezone.utc).timestamp()
        param = datetime.date(datetime.fromtimestamp(lastupdate)).strftime("%s")
        collection = context().drm_server.get_collection(drm_server_endpoint, param)
        data = []
        for obj in collection:
            res = eval('self.data_handler.handle_%s(obj)' % drm_server_endpoint)
            if res:
                data.append(res)
        if name:
            if name == 'ipaddress':
                data = list({d['_key']: d for d in data}.values())
        self.send_data(name, data)

    def get_new_model_state_id(self):
        return context().drm_server.get_model_state_id()

    # Import all vertices from data source
    def import_vertices(self):
        for drm_server_endpoint, data_name in endpoint_mapping.items():
            self.import_collection(drm_server_endpoint, data_name)

    # Imports edges for all collection
    def import_edges(self):
        for drm_server_endpoint, data_name in self.data_handler.edges.items():
            self.import_collection(drm_server_endpoint, data_name)
