from util import DB_READY, FAILURE


BATCH_SIZE = 20


class FullImport(object):
    def __init__(self, context):
        self.context = context
        self.statuses = []


    def init(self):
        db_status = self.context.car_service.get_db_status()
        if db_status != DB_READY:
            print('Database is not ready.')
            exit(1)
        source_report_data = {'source': self.source, 'report': self.report, 'source_report': self.source_report}
        status = self.context.car_service.import_data(source_report_data)
        if status.status == FAILURE:
            print('Error: ' + status.error)
            exit(1)
        self.statuses.append(status)
        self.wait_for_completion_of_import_jobs()
        self.context.car_service.enter_full_import_in_progress_state()


    def complete(self):
        self.context.car_service.exit_full_import_in_progress_state()
        print('Done.')


    def wait_for_completion_of_import_jobs(self):
        self.context.car_service.check_import_status(self.statuses)
        for status in self.statuses:
            if status.status == FAILURE:
                print('Error: ' + status.error)
                exit(1)
        self.statuses = []


    def send_data(self, name, data):
        envelope = {'report': self.report, 'source': self.source, 'source_report': self.source_report, name: data}
        status = self.context.car_service.import_data(envelope)
        if status.status == FAILURE:
            print('Error: ' + status.error)
            exit(1)
        self.statuses.append(status)
        if len(self.statuses) == BATCH_SIZE:
            self.wait_for_completion_of_import_jobs()


    def run(self):
        self.init()
        self.import_vertices()
        self.wait_for_completion_of_import_jobs()
        self.import_edges()
        self.wait_for_completion_of_import_jobs()
        self.complete()
