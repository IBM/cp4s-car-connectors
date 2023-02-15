
from car_framework.full_import import BaseFullImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping, epoch_to_datetime_conv
import json, datetime
from base64 import b64encode


class FullImport(BaseFullImport):
    """Full Import"""
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Logic to import a collection; called by import_vertices
    def import_collection(self):
        """
        Process the api response and creates initial import collections
        """
        context().logger.debug('Import collection started')

        three_months_back = epoch_to_datetime_conv(self.data_handler.timestamp) - datetime.timedelta(days=90)
        three_months_back = three_months_back.isoformat() 
        query = {
            'condition': "AND",
            'rules': [
                {
                  'field': "table.target_last_seen",
                  'operator': "greater_or_equal",
                  'value': three_months_back
                  # pull in all Randori informaiton for assets scanned over the last three months 
                 }             
            ]
        }
        # We need the query to be a string in order to base64 encode it easily
        query = json.dumps(query)

        # Randori expects the 'q' query to be base64 encoded in string format
        query = b64encode(query.encode()).decode()

        # this need to be implemeted as we build data handler
        allDetectionsForTarget = context().asset_server.get_detections_for_target(offset=1, limit=100, sort=["last_seen"], q=query, reversed_nulls=True)

        for detection in allDetectionsForTarget.data:
            for node in endpoint_mapping["get_detections_for_target"]:
                getattr(self.data_handler, 'handle_' + node.lower())(detection)

    # Get save point from server
    def get_new_model_state_id(self):
        # If server doesn't have save point it can just return current time
        # So that it can be used for next incremental import
        return str(self.data_handler.timestamp)

    # Import all vertices from data source
    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()
