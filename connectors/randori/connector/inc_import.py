from car_framework.inc_import import BaseIncrementalImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping, epoch_to_datetime_conv
import json, datetime
from base64 import b64encode

class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        # initialize the data handler.
        # If data source doesn't have external reference property None can be supplied as parameter.
        self.data_handler = DataHandler()
        super().__init__()
        self.create_source_report_object()

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source and report entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

# Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.last_model_state_id = last_model_state_id

    # Import all vertices from data source
    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()

    # Logic to import a collection; called by import_vertices
    def import_collection(self):
        """
        Process the api response and creates initial import collections
        """
        context().logger.debug('Import collection started')

        last_run = epoch_to_datetime_conv(self.last_model_state_id).isoformat()

        query = {
            'condition': "AND",
            'rules': [
                        {
                            'field': "table.target_last_seen",
                            'operator': "greater_or_equal",
                            'value': last_run
                            # pull in Randori information when last_seen > the last_run
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

    def delete_vertices(self):
        pass
