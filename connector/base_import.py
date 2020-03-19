from util import FAILURE, BATCH_SIZE

class BaseImport(object):

    def __init__(self, context):
        self.context = context
        self.statuses = []


    def wait_for_completion_of_import_jobs(self):
        self.context.car_service.check_import_status(self.statuses)
        for status in self.statuses:
            if status.status == FAILURE:
                print('Error: ' + status.error)
                exit(1)
        self.statuses = []


    def send_data(self, name, data):
        envelope = self.create_source_report_object()
        envelope[name] = data
        status = self.context.car_service.import_data(envelope)
        if status.status == FAILURE:
            print('Error: ' + status.error)
            exit(1)
        self.statuses.append(status)
        if len(self.statuses) == BATCH_SIZE:
            self.wait_for_completion_of_import_jobs()
