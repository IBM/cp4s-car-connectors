import string
import requests
import datetime
import json
from car_framework.context import context

from requests_toolbelt.multipart.encoder import MultipartEncoder


class DRMServer(object):

    def __init__(self):
        self.tenant_bearer_token_url = '/user/login'
        self.drm_endpoint_url = '/restAPI/v2/delta/enterprise/concept/car/'
        self.multipart_data = MultipartEncoder(
            fields={'username': context().args.username, 'password': context().args.password, 'deviceid': 'device1',
                    'clientDetails': '{"ipAddress":"192.168.0.26","macAddress":"e4:ce:8f:40:62:64"}'})
        self.collection_multipart_data = {
            'clientDetails': '{"macAddress":"No Mac","ipAddress":"No IP","deviceId":'
                             '"JDJhJDEwJFAyajRiczl5U1lUQy5ueEFrSHJzcWU3SDJDL1J1WUJMbDFOamxLb2ZZazVPaVU5d0RObDVl"}',
            'filterFields': '{"includeProperty":true}',
            'forEdges': 'false',
            'forDeleted': '0'
        }
        self.server_headers_bearer = {'Content-Type': self.multipart_data.content_type}
        self.auth = self.get_bearer_Token()
        self.csrf = string.ascii_lowercase
        cookie = {'Cookie': 'CSRF-TOKEN='}
        cookie['Cookie'] += self.csrf
        self.headers = {'Authorization': self.auth, 'X-CSRF-TOKEN': self.csrf}
        self.headers.update(cookie)
        self.cache = {}

    # Get the bearer Token from IBM Security Verify tenant using username and password
    # Use this bearer token to make REST API calls
    def get_bearer_Token(self):
        context().logger.info('Fetching the Authorization bearer token for tenant :  ' + str('%s' % (context().args.tenantUrl)))
        context().logger.info('%s%s' % (context().args.tenantUrl, self.tenant_bearer_token_url))
        resp = requests.post('%s%s' % (context().args.tenantUrl, self.tenant_bearer_token_url),
                             data=self.multipart_data,
                             headers=self.server_headers_bearer, verify=False)
        if resp.status_code != 200:
            raise Exception('Error when getting authorization bearer token: %s' % resp.status_code)
        bearer_token = 'Bearer' + " " + resp.json()['data']['access_token']
        return bearer_token

    # Pulls data for all collection entities
    def get_collection(self, drm_server_endpoint, param):
        url = context().args.tenantUrl + str(self.drm_endpoint_url)
        context().logger.info('DRM endpoint url : ' + str('%s%s' % (url, drm_server_endpoint)))
        if drm_server_endpoint == 'DSAPPLICATION' or drm_server_endpoint == 'ApplicationBPMapping':
            self.collection_multipart_data['forEdges'] = 'true'
        else:
            self.collection_multipart_data['forEdges'] = 'false'
        context().logger.info(self.collection_multipart_data)
        # print(self.collection_multipart_data)
        temp = json.loads(self.collection_multipart_data['filterFields'])
        temp['lastUpdatedTime'] = param
        temp['pageNo'] = 0
        if context().args.pageSize is None:
            temp['pageSize'] = 100
        else:
            temp['pageSize'] = int(context().args.pageSize)
        self.collection_multipart_data['filterFields'] = json.dumps(temp)
        try:
            json_data = []
            while True:
                self.collection_multipart_data['filterFields'] = json.dumps(temp)
                data = self.get_total_records(url, drm_server_endpoint)
                json_data.extend(data)
                if len(data) < temp['pageSize']:
                    break
                else:
                    temp['pageNo'] += 1
        except Exception as ex:
            raise Exception(str(ex))
        return json_data

    # Pulls the total Record from the DRM database
    def get_total_records(self, url, drm_server_endpoint):
        payload = MultipartEncoder(fields=self.collection_multipart_data)
        self.headers.update({'Content-Type': payload.content_type})
        resp = requests.post("%s%s" % (url, drm_server_endpoint), data=payload, headers=self.headers, verify=False)
        if resp.status_code != 200:
            raise Exception('Error when getting resources: %s' % resp.status_code)
        json_data = resp.json()['data']
        if json_data is None:
            json_data = []
        return json_data

    def get_deleted_collection(self, drm_server_endpoint, param):
        url = context().args.tenantUrl + str(self.drm_endpoint_url)
        context().logger.info('DRM Delete endpoint url : ' + str('%s%s' % (url, drm_server_endpoint)))
        if drm_server_endpoint == 'DSAPPLICATION' or drm_server_endpoint == 'ApplicationBPMapping':
            self.collection_multipart_data['forEdges'] = 'true'
        else:
            self.collection_multipart_data['forEdges'] = 'false'
        context().logger.info(self.collection_multipart_data)
        temp = json.loads(self.collection_multipart_data['filterFields'])
        temp['lastUpdatedTime'] = param
        temp['pageNo'] = 0
        if context().args.pageSize is None:
            temp['pageSize'] = 100
        else:
            temp['pageSize'] = int(context().args.pageSize)
        self.collection_multipart_data['filterFields'] = json.dumps(temp)
        self.collection_multipart_data['forDeleted'] = '1'
        try:
            json_data = []
            while True:
                self.collection_multipart_data['filterFields'] = json.dumps(temp)
                data = self.get_total_records(url, drm_server_endpoint)
                json_data.extend(data)
                if len(data) < temp['pageSize']:
                    break
                else:
                    temp['pageNo'] += 1
        except Exception as ex:
            raise Exception(str(ex))
        return json_data

    def _cache(self, endpoint, obj):
        id = obj.get('pk')
        if id:
            self.cache['%s/%s/%s/' % (context().args.server, endpoint, id)] = obj

    def get_model_state_id(self):
        return int(datetime.datetime.now().timestamp() * 1000)

    # This function is not required in our implementation
    def get_model_state_delta(self, last_model_state_id, new_model_state_id):
        pass
