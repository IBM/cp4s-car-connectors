from datetime import datetime, timedelta
from connector.data_handler import DataHandler, endpoint_mapping
from car_framework.full_import import BaseFullImport
from car_framework.context import context


class FullImport(BaseFullImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        # Get arguments from config
        self.config = context().asset_server.config

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Get threat events
    def get_threat_events(self, asset_server_endpoint):
        """
        Fetch the threats for SIEM api.
        parameters:
            asset_server_endpoint(str): server endpoint
        returns:
            collection(list): SIEM api response
        """
        collection = []
        current_time = datetime.utcnow()
        start_time = current_time - timedelta(days=self.config['parameter']['interval_days'])
        while start_time < current_time:
            next_hour = start_time + timedelta(hours=1)
            if next_hour > current_time:
                next_hour = current_time
            end_point = "%s?format=%s&interval=%s/%s" % (self.config['endpoint'][asset_server_endpoint],
                                                         self.config['parameter']['format'],
                                                         start_time.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                                                         next_hour.strftime('%Y-%m-%dT%H:%M:%S') + 'Z')
            try:
                events = context().asset_server.get_collection(end_point)
                collection = collection + events['messagesDelivered'] + events['messagesBlocked']
            except Exception as e:
                message = str(e)
                # Increasing the start time by 3 sec if query time is in past interval.
                if "The requested start time is too far into the past" in message:
                    start_time = start_time + timedelta(seconds=3)
                    continue
                raise Exception(e)

            start_time = next_hour
        return collection

    # Logic to import a collection; called by import_vertices
    def import_collection(self, asset_server_endpoint, resource):
        """
        It will process the api response and creates initial import collections
        parameters:
            asset_server_endpoint(str): key for identify the api
            resource(list):  entities
        returns:
            None
        """
        collection = []
        context().logger.debug('Import collection started for %s', asset_server_endpoint)

        if asset_server_endpoint == 'siem':
            collection = self.get_threat_events(asset_server_endpoint)
            context().logger.info('The number of siem events: %s', len(collection))
        else:
            asset_server_endpoint = "%s?window=%s" % (self.config['endpoint'][asset_server_endpoint],
                                                      self.config['parameter']['time_window'])
            collection = context().asset_server.get_collection(asset_server_endpoint)
            collection = collection['users']
            context().logger.info('The number of people : %s', len(collection))

        if collection:
            for node in resource:
                for obj in collection:
                    getattr(self.data_handler, 'handle_' + node.lower())(obj)

    # Get save point from server
    def get_new_model_state_id(self):
        # If server doesn't have save point it can just return current time
        # So that it can be used for next incremental import
        return str(self.data_handler.timestamp)

    # Import all vertices from data source
    def import_vertices(self):
        context().logger.debug('Import vertices started')
        for asset_server_endpoint, data_name in endpoint_mapping.items():
            self.import_collection(asset_server_endpoint, data_name)

        self.data_handler.send_collections(self)

    # Imports edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()
