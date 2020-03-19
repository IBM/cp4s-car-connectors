from util import DB_READY, FAILURE
from base_import import BaseImport



class FullImport(BaseImport):
    def __init__(self, context):
        super().__init__(context)
        self.statuses = []


    def init(self):
        db_status = self.context.car_service.get_db_status()
        if db_status != DB_READY:
            print('Database is not ready.')
            exit(1)
        source_report_data = self.create_source_report_object()
        status = self.context.car_service.import_data(source_report_data)
        if status.status == FAILURE:
            print('Error: ' + status.error)
            exit(1)
        self.statuses.append(status)
        self.wait_for_completion_of_import_jobs()
        self.context.car_service.enter_full_import_in_progress_state()
        self.new_model_state_id = self.get_new_model_state_id()


    def complete(self):
        self.context.car_service.exit_full_import_in_progress_state()
        self.save_new_model_state_id(self.new_model_state_id)
        print('Done.')


    def run(self):
        self.init()
        self.import_vertices()
        self.wait_for_completion_of_import_jobs()
        self.import_edges()
        self.wait_for_completion_of_import_jobs()
        self.complete()
