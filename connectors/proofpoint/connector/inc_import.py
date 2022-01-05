from connector.data_handler import DataHandler, endpoint_mapping
from car_framework.context import context
from car_framework.inc_import import BaseIncrementalImport


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        self.create_source_report_object()
        self.car_active_edge = ''
        # Get arguments from config
        self.config = context().asset_server.config
        self.active_vulnerability = self.get_active_vulnerability()

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.delta = context().asset_server.get_model_state_delta(last_model_state_id, new_model_state_id)
        self.last_model_state_id = last_model_state_id

    @staticmethod
    def get_active_vulnerability():

        response = context().car_service.graph_attribute_search('vulnerability', 'source',
                                                                context().args.source)
        active_vulnerability = []
        for row in response:
            active_vulnerability.append(row['external_id'])

        return active_vulnerability

    def import_collection(self, asset_server_endpoint, car_resource_name):
        """
        It will process the api response and does following operations
        Incremental create, Incremental update, Incremental delete
        parameters:
            asset_server_endpoint(str): key for identify the api
            car_resource_name(list):  entities
        returns:
            None
        """
        updates = self.delta.get(asset_server_endpoint)

        # processing SIEM api response
        if asset_server_endpoint == 'siem':

            for row in updates:

                for obj in row['events']:

                    for threat in obj['threatsInfoMap']:

                        # skip the existing vulnerabilities
                        if threat['threatID'] in self.active_vulnerability:
                            continue

                        # incremental create
                        data = obj
                        data['threatsInfoMap'] = [threat]

                        for event in car_resource_name:
                            getattr(self.data_handler, 'handle_' + event.lower())(data)

                # incremental update use click event records
                self.incremental_update(row['clicks'])

        # processing people api response
        else:
            for obj in updates:
                for event in car_resource_name:
                    getattr(self.data_handler, 'handle_' + event.lower())(obj)

    def incremental_update(self, click_events):
        """
         Function performs incremental update
         parameters:
             recipient(str): user detail
             click_events(list):  click event details
             threat(dict): api response
         returns:
             None
         """
        for click_event in click_events:

            # check the threat already present in the db.
            if click_event['threatID'] in self.active_vulnerability:

                edge = {'_from_external_id': click_event['recipient'],
                        '_to_external_id': click_event['threatID'],
                        'last_modified': click_event['clickTime']}
                self.data_handler.add_edge('asset_vulnerability', edge)

    # Import all vertices from data source
    def import_vertices(self):
        for asset_server_endpoint, car_resource_name in endpoint_mapping.items():
            self.import_collection(asset_server_endpoint, car_resource_name)
        self.data_handler.send_collections(self)

    # Imports edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)

    # Delete vertices that are deleted in data source
    def delete_vertices(self):
        """
        It will check the threat status
        If it's cleared delete the vulnerability
        parameters:
                None
        returns:
            None
        """
        deletions = []

        context().logger.debug('Delete vertices started')

        for external_id in self.active_vulnerability:

            try:
                threat_status = context().asset_server.get_collection(self.config['endpoint']['threat'] +
                                                                      external_id)
            except Exception as e:
                if 'threatId not found' in str(e):
                    context().logger.info('%s Threat id %s not found, continuing the process:' % (str(e), external_id))
                    continue

            if threat_status.get('status') == 'cleared':
                deletions.append(external_id)

        context().car_service.delete('vulnerability', deletions)
