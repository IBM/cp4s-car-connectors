from car_framework.inc_import import BaseIncrementalImport
from car_framework.context import context
from connector.data_handler import DataHandler
from car_framework.util import IncrementalImportNotPossible

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

    # To disbale incremental import
    def run(self):
        raise IncrementalImportNotPossible('Need to be implemented.')