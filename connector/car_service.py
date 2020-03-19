import requests, json, urllib
from util import get_json, Status, SUCCESS, FAILURE, IN_PROGRESS, DB_FAILURE, DB_READY

IMPORT_RESOURCE = '/imports'
STATUS_RESOURCE = '/importstatus'
DATABASE_RESOURCE = '/databases'
JOBSTATUS_RESOURCE = '/jobstatus'
SOURCE_RESOURCE = '/source'

FULL_IMPORT_IN_PROGRESS_ENDPOINT = '/full-import-in-progress'
MODEL_STATE_ID = 'model_state_id'
max_wait_time = 60


class CarService(object):

    def __init__(self, context):
        self.context = context
        self.import_url = context.args.car_service + IMPORT_RESOURCE
        self.status_url = context.args.car_service + STATUS_RESOURCE
        self.job_status_url = context.args.car_service + JOBSTATUS_RESOURCE
        self.headers =  {'Accept' : 'application/json', 'Content-Type' : 'application/json'}


    def get_last_model_state_id(self):
        url = '%s/source/%s/graph' % (self.context.args.car_service, urllib.parse.quote_plus(self.context.source))
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            return None
        json_data = resp.json()
        return json_data.get('result') and json_data.get('result').get(MODEL_STATE_ID)


    def save_new_model_state_id(self, new_model_state_id):
        data = json.dumps({ MODEL_STATE_ID: new_model_state_id })
        resp = requests.patch(self.context.args.car_service + SOURCE_RESOURCE, data=data, params={ 'key': self.context.source }, headers=self.headers)
        if resp.status_code != 200:
            raise Exception('Error when trying to save a save point: %d' % resp.status_code)


    def import_data(self, data):
        status = Status()
        try:
            json_data = json.dumps(data)
            resp = requests.post(self.import_url, data=json_data, headers=self.headers)
            status.status_code = resp.status_code
            json_resp = get_json(resp)
            if 'id' in json_resp:
                status.job_id = json_resp['id']
                status.status = IN_PROGRESS
            else:
                status.status = FAILURE
                status.error = str(json_resp)
            return status

        except Exception as e:
            status.status = FAILURE
            status.error = str(e)
            return status


    def check_import_status(self, statuses):
        # for IN_PROGRESS statuses create a map: id -> status
        jobs_to_check = dict(map(lambda s: (s.job_id, s), filter(lambda s: s.status is IN_PROGRESS, statuses)))
        
        wait_time = 1
        try:
            while True:
                if not jobs_to_check: return
                params = ','.join(jobs_to_check.keys())
                resp = requests.get(self.status_url, params={'ids': params}, headers=self.headers)
                data = get_json(resp)
                if 'error_imports' in data:
                    for err in data['error_imports']:
                        id = err['id']
                        jobs_to_check[id].status = FAILURE
                        jobs_to_check[id].error = err.get('error')
                        jobs_to_check[id].status_code = err.get('statusCode')
                        jobs_to_check.pop(id, None)

                incomplete_ids = []
                if 'incomplete_imports' in data:
                    incomplete = data['incomplete_imports']
                    if incomplete:
                        print('The following imports are still in progress:')
                        incomplete_ids = map(lambda item: item['id'], incomplete)
                        for id in incomplete_ids:
                            print('id: %s' % id)

                done = filter(lambda id: id not in incomplete_ids, list(jobs_to_check.keys()))
                for id in done:
                    jobs_to_check[id].status = SUCCESS
                    del jobs_to_check[id]

                if not jobs_to_check: return
                time.sleep(wait_time)
                if wait_time < max_wait_time: wait_time *= 2
                if wait_time > max_wait_time: wait_time = max_wait_time

        except Exception as e:
            # mark all remaining statuses as failed
            for s in jobs_to_check.values():
                s.status = FAILURE
                s.error = str(e)
        

    def delete(self, resource, ids):
        url = '%s/source/%s/%s?external_ids=%s' % (self.context.args.car_service, self.context.source, resource, ids)
        r = requests.delete(url, headers=self.headers)
        return r.status_code


    '''
    algorithm:
        1. Call GET /databases endpoint and check if Database exist with the checks of all the collections, indexes, etc
            - Yes: move on and start importing
            - No: Call the endpoint POST /databases, the function should wait here untill the database, graph, indexes are created, this will take more than 10 minutes
    '''
    def get_db_status(self):
        db_url = self.context.args.car_service + DATABASE_RESOURCE
        r = requests.get(db_url)
        status_code = r.status_code
        
        if status_code == 400:
            # the database is not setup yet, create it
            r = requests.post(db_url)
            job_id = get_json(r)['job_id']
            status = self.wait_until_done(job_id)
            # status could be either COMPLETE or ERROR
            if status == 'COMPLETE':
                return DB_READY
            else:
                for x in range(5):
                    if self._get_db_status() == DB_READY:
                        return DB_READY
                    time.sleep(10)
                return DB_FAILURE
        
        elif status_code == 200:
            r_json = get_json(r)
            databases = r_json['databases']
            if databases[0]['is_ready'] == True:
                # database is ready to accept imports
                return DB_READY
            elif databases[0]['graph_name'] == '':
                # create the graph
                payload = json.dumps({ 'graph_name': 'assets'})
                r = requests.patch(db_url, data=payload, headers=self.headers)
                job_id = get_json(r)['job_id']
                status = self.wait_until_done(job_id)
                # status could be either COMPLETE or ERROR
                if status == 'COMPLETE':
                    return DB_READY
                else:
                    return DB_FAILURE
            elif len(databases[0]['collections_without_indexes']) > 0:
                payload = json.dumps({ 'collections_without_indexes': databases[0]['collections_without_indexes']})
                r = requests.patch(db_url, data=payload, headers=self.headers)
                job_id = get_json(r)['job_id']
                status = self.wait_until_done(job_id)
                # status could be either COMPLETE or ERROR
                if status == 'COMPLETE':
                    return DB_READY
                else:
                    return DB_FAILURE
        
        elif recoverable_failure_status_code(status_code):
            raise RecoverableFailure('Getting the following status code when accessing ISC CAR service: %d' % status_code)
        else:
            raise UnrecoverableFailure('Getting the following status code when accessing ISC CAR service: %d' % status_code)

    def wait_until_done(self, job_id):
        job_complete = False
        status = 'INPROGRESS'
        while not job_complete:
            r = requests.get(self.job_status_url + '/{}'.format(job_id), headers=self.headers)
            if r.status_code == 200:
                status = get_json(r)['status']
                if status == 'COMPLETE' or status == 'ERROR':
                    job_complete = True
            else:
                return 'ERROR'

        return status


    def enter_full_import_in_progress_state(self):
        endpoint = '%s/source/%s%s' % (self.context.args.car_service, self.context.source, FULL_IMPORT_IN_PROGRESS_ENDPOINT)
        r = requests.post(endpoint, headers=self.headers)
        return r.status_code


    def exit_full_import_in_progress_state(self):
        endpoint = '%s/source/%s%s' % (self.context.args.car_service, self.context.source, FULL_IMPORT_IN_PROGRESS_ENDPOINT)
        r = requests.delete(endpoint, headers=self.headers)
        return r.status_code

