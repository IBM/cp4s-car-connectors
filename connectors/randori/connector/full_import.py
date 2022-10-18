
from car_framework.full_import import BaseFullImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping
import json
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

        query = "eyJjb25kaXRpb24iOiJBTkQiLCJydWxlcyI6W3siY29uZGl0aW9uIjoiT1IiLCJydWxlcyI6W3sibGFiZWwiOiJtZWRpdW0iLCJjb25kaXRpb24iOiJBTkQiLCJydWxlcyI6W3siaWQiOiJ0YWJsZS5jb25maWRlbmNlIiwiZmllbGQiOiJ0YWJsZS5jb25maWRlbmNlIiwidHlwZSI6ImludGVnZXIiLCJpbnB1dCI6Im51bWJlciIsIm9wZXJhdG9yIjoiZ3JlYXRlcl9vcl9lcXVhbCIsInZhbHVlIjo2MH0seyJpZCI6InRhYmxlLmNvbmZpZGVuY2UiLCJmaWVsZCI6InRhYmxlLmNvbmZpZGVuY2UiLCJ0eXBlIjoiaW50ZWdlciIsImlucHV0IjoibnVtYmVyIiwib3BlcmF0b3IiOiJsZXNzX29yX2VxdWFsIiwidmFsdWUiOjc0fV19LHsibGFiZWwiOiJoaWdoIiwiY29uZGl0aW9uIjoiQU5EIiwicnVsZXMiOlt7ImlkIjoidGFibGUuY29uZmlkZW5jZSIsImZpZWxkIjoidGFibGUuY29uZmlkZW5jZSIsInR5cGUiOiJpbnRlZ2VyIiwiaW5wdXQiOiJudW1iZXIiLCJvcGVyYXRvciI6ImdyZWF0ZXJfb3JfZXF1YWwiLCJ2YWx1ZSI6NzV9LHsiaWQiOiJ0YWJsZS5jb25maWRlbmNlIiwiZmllbGQiOiJ0YWJsZS5jb25maWRlbmNlIiwidHlwZSI6ImludGVnZXIiLCJpbnB1dCI6Im51bWJlciIsIm9wZXJhdG9yIjoibGVzc19vcl9lcXVhbCIsInZhbHVlIjoxMDB9XX1dLCJ1aV9pZCI6ImNvbmZpZGVuY2UifSx7InVpX2lkIjoidW5hZmZpbGlhdGVkIiwiY29uZGl0aW9uIjoiT1IiLCJydWxlcyI6W3sidWlfaWQiOiJzaG93X25vX2FmZmlsaWF0aW9uIiwiaWQiOiJ0YWJsZS5hZmZpbGlhdGlvbl9zdGF0ZSIsImZpZWxkIjoidGFibGUuYWZmaWxpYXRpb25fc3RhdGUiLCJ0eXBlIjoib2JqZWN0IiwiaW5wdXQiOiJ0ZXh0Iiwib3BlcmF0b3IiOiJlcXVhbCIsInZhbHVlIjoiTm9uZSJ9XX1dLCJ1aV9pZCI6ImJhc2UifQ=="

        # # We need the query to be a string in order to base64 encode it easily
        # query = json.dumps(query)

        # # Randori expects the 'q' query string to be base64 encoded
        # query = b64encode(query.encode())

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