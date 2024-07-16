import json
import time

import requests, urllib3
import xmltodict
from requests.auth import HTTPBasicAuth
from car_framework.context import context
from connector.error_response import ErrorResponder
from connector.data_handler import epoch_to_datetime_conv, append_vuln_in_asset, deep_get


class AssetServer(object):

    def __init__(self):

        # Get server connection arguments from config file
        with open('connector/qualys_config.json', 'rb') as json_data:
            self.config = json.load(json_data)
        self.basic_auth = HTTPBasicAuth(context().args.username,
                                        context().args.password)

    # Pulls asset data for all collection entities
    def get_collection(self, asset_server_endpoint, headers=None, auth=None, data=None):
        """
        Fetch data from datasource using api
        parameters:
            asset_server_endpoint(str): api end point
            data(str): api input
        returns:
            json_data(dict): Api response
        """
        tries = 0
        while tries < 3:
            tries += 1
            try:
                resp = requests.post(asset_server_endpoint, headers=headers, auth=auth, data=data)
            # continue to try when timeout happens
            except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
                context().logger.error("get_collection timeout error, retry after 3 seconds", e)
                time.sleep(3)
                continue

            except Exception as ex:
                return_obj = {}
                ErrorResponder.fill_error(return_obj, ex)
                raise Exception(return_obj)

            return resp

    def get_assets(self, last_model_state_id=None):
        """
        Fetch the entire asset records from data source using pagination.
        parameters:
            asset_server_endpoint(str): api end point
            last_model_state_id(datetime): last run time
        returns:
            results(list): Api response
        """
        results = []
        pagination = self.config['parameter']['pagination']['enabled']
        page_size = self.config['parameter']['pagination']['page_size']
        headers = self.config['parameter']['headers']
        auth = self.basic_auth
        asset_server_endpoint = context().args.server + self.config['endpoint']['asset']

        # limit number of results
        data = '<ServiceRequest>' \
               '<preferences><limitResults>%s</limitResults></preferences>' \
               '</ServiceRequest>' % page_size

        # adding filter for incremental run
        if last_model_state_id:
            data = '<ServiceRequest>' \
                   '<preferences><limitResults>%s</limitResults></preferences>' \
                   '<filters><Criteria field="updated" operator="GREATER">%s</Criteria></filters>' \
                   '</ServiceRequest>' % (page_size, last_model_state_id)

        while pagination:
            response = self.get_collection(asset_server_endpoint, headers=headers, auth=auth, data=data)
            response_json = response.json()
            if response.status_code != 200 or response_json['ServiceResponse']['responseCode'] != 'SUCCESS':
                return_obj, error_msg = {}, {}
                status_code = response_json['ServiceResponse']['responseCode']
                error_msg['message'] = response_json['ServiceResponse']['responseErrorDetails']
                ErrorResponder.fill_error(return_obj, json.dumps(error_msg).encode(), status_code)
                raise Exception(return_obj)

            if response_json['ServiceResponse'].get('data'):
                results = results + response_json['ServiceResponse']['data']

            # check previous api call response hasMoreRecords
            if response_json['ServiceResponse'].get('hasMoreRecords') and \
                    response_json['ServiceResponse']['hasMoreRecords'] == 'true':

                # adding filter and pagination for incremental run
                if last_model_state_id:
                    data = '<ServiceRequest>' \
                           '<preferences><startFromOffset>%s</startFromOffset>' \
                           '<limitResults>%s</limitResults></preferences>' \
                           '<filters><Criteria field="updated" operator="GREATER">%s</Criteria></filters>' \
                           '</ServiceRequest>' % (len(results) + 1, page_size, last_model_state_id)
                else:  # adding filter and pagination for full import
                    data = '<ServiceRequest>' \
                           '<preferences><startFromOffset>%s</startFromOffset>' \
                           '<limitResults>%s</limitResults></preferences>' \
                           '</ServiceRequest>' % (len(results) + 1, page_size)
            else:
                pagination = False

        return results

    def get_vulnerabilities(self):
        """
        Fetch the entire vulnerability  records from data source using pagination.
        returns:
            results(list): Api response
        """
        data = None
        results = []
        pagination = self.config['parameter']['pagination']['enabled']
        page_size = self.config['parameter']['pagination']['page_size']
        headers = self.config['parameter']['headers']
        auth = self.basic_auth
        server_endpoint = context().args.server + self.config['endpoint']['asset_vulnerability']
        server_endpoint = server_endpoint + "&truncation_limit=" + str(page_size) if pagination else server_endpoint

        while pagination:
            response = self.get_collection(server_endpoint, headers=headers, auth=auth, data=data)

            if response.status_code == 409:
                ratelimit_to_wait = int(response.headers['X-RateLimit-ToWait-Sec'])
                context().logger.debug('API Rate limit reached, sleeping for %s seconds' % ratelimit_to_wait)
                time.sleep(ratelimit_to_wait)
                continue

            elif response.status_code != 200:
                response = xmltodict.parse(response.text)
                return_obj = {}
                status_code = response['SIMPLE_RETURN']['RESPONSE']['CODE']
                error_message = response['SIMPLE_RETURN']['RESPONSE']['TEXT']
                ErrorResponder.fill_error(return_obj, error_message.encode('utf'), status_code)
                raise Exception(return_obj)

            response = xmltodict.parse(response.text)

            if response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE'].get('HOST_LIST'):
                if isinstance(response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']['HOST_LIST']['HOST'], list):
                    results = results + response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']['HOST_LIST']['HOST']
                else:
                    temp = []
                    temp.append(response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']['HOST_LIST']['HOST'])
                    results = results + temp
            # check the response has more records, will use the link.
            if 'WARNING' in response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']:
                server_endpoint = response['HOST_LIST_VM_DETECTION_OUTPUT']['RESPONSE']['WARNING']['URL']
            else:
                pagination = False

        # Update host vulnerability detections with vulnerability knowledgebase information
        if results:
            self.add_vuln_kb_info(results)
        return results

    def add_vuln_kb_info(self, host_vuln_detections):
        """
        Add vulnerability knowledgebase information to host detection list
        info added to vulnerability detections like {'<QID>' : '<QID knowledgebase details>'}
        """
        vuln_list = []
        # Get the list of vulnerabilities from the detection
        for host_vuln_detection in host_vuln_detections:
            host_vuln_list = deep_get(host_vuln_detection, ['DETECTION_LIST', 'DETECTION'], [])
            if host_vuln_list and not isinstance(host_vuln_list, list):
                host_vuln_list = [host_vuln_list]
            vuln_list = vuln_list + [vuln['QID'] for vuln in host_vuln_list]
        vuln_list = set(vuln_list)

        # Get the vulnerability information from knowledgebase
        knowledge_base_vuln_list = self.get_knowledge_base_vuln_list(vuln_list)
        knowledge_base_vuln_list = {vuln['QID']: vuln for vuln in knowledge_base_vuln_list}

        # Add Knowledge base vuln info to host detection vulnerabilities
        for host_vuln_detection in host_vuln_detections:
            host_vuln_list = deep_get(host_vuln_detection, ['DETECTION_LIST', 'DETECTION'], [])
            if host_vuln_list and not isinstance(host_vuln_list, list):
                qid = host_vuln_detection['DETECTION_LIST']['DETECTION']['QID']
                host_vuln_detection['DETECTION_LIST']['DETECTION'][qid] = knowledge_base_vuln_list.get(qid)
            else:
                for i in range(0, len(host_vuln_detection['DETECTION_LIST']['DETECTION'])):
                    qid = host_vuln_detection['DETECTION_LIST']['DETECTION'][i]['QID']
                    host_vuln_detection['DETECTION_LIST']['DETECTION'][i][qid] = knowledge_base_vuln_list.get(qid)

    def get_knowledge_base_vuln_list(self, qid_list):
        """
        Get QID associated CVE and general information from Qualys knowledgebase
        """
        qid_list = list(set(qid_list))
        headers = self.config['parameter']['headers']
        auth = self.basic_auth
        chunk_size = self.config['qid_size']
        server_endpoint = context().args.server + self.config['endpoint']['vuln_knowledgebase']
        results = []

        for i in range(0, len(qid_list), chunk_size):
            chunk_server_endpoint = server_endpoint + '&ids=' + ','.join(qid_list[i:i + chunk_size])
            try:
                response = self.get_collection(chunk_server_endpoint, headers=headers, auth=auth)
                if response.status_code != 200:
                    response = xmltodict.parse(response.text)
                    return_obj = {}
                    status_code = response['SIMPLE_RETURN']['RESPONSE']['CODE']
                    error_message = response['SIMPLE_RETURN']['RESPONSE']['TEXT']
                    ErrorResponder.fill_error(return_obj, error_message.encode('utf'), status_code)
                    raise Exception(return_obj)
                else:
                    response = xmltodict.parse(response.text)
                    knowledge_base_vuln_list = deep_get(response,
                                                        ['KNOWLEDGE_BASE_VULN_LIST_OUTPUT', 'RESPONSE', 'VULN_LIST',
                                                         'VULN'], [])
                    if knowledge_base_vuln_list and not isinstance(knowledge_base_vuln_list, list):
                        knowledge_base_vuln_list = [knowledge_base_vuln_list]
                    results = results + knowledge_base_vuln_list
                    break
            except Exception as e:
                return_obj = {}
                ErrorResponder.fill_error(return_obj, e)
                raise Exception(return_obj)

        return results

    def get_bearer_token(self):
        """
        Generate bearer token using credentials
        :return: Bearer token
        """
        endpoint = context().args.gateway + self.config['endpoint']['auth']
        payload= {'username': context().args.username, 'password':context().args.password, 'token':'true'}
        data = urllib3.request.urlencode(payload)
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        response = self.get_collection(endpoint, headers=header, data=data)
        # on successful token generation 201 status code will be returned
        if response.status_code != 201:
            response_json = response.json()
            return_obj, error_msg = {}, {}
            status_code = response.status_code
            error_msg['message'] = response_json.get('message')
            ErrorResponder.fill_error(return_obj, json.dumps(error_msg).encode(), status_code)
            raise Exception(return_obj)
        return response.text

    def get_applications(self, last_model_state_id=None):
        """
        Fetch the application records from data source using pagination.
        parameters:
            last_model_state_id: last import time
        returns:
            results(list): Api response
        """

        pagination = True
        results = []
        data = None
        token = self.get_bearer_token()
        headers = {"Authorization": "Bearer %s" % token}
        asset_server_endpoint = context().args.gateway + self.config['endpoint']['applications']
        if last_model_state_id:
            asset_server_endpoint = asset_server_endpoint + '&assetLastUpdated=%s' % last_model_state_id
        server_endpoint = asset_server_endpoint
        response_json = None
        while pagination:
            response = self.get_collection(server_endpoint, headers=headers, data=data)
            if response.text:
                response_json = response.json()
                if response.status_code not in [200, 204] or response_json['responseCode'] != 'SUCCESS':
                    return_obj, error_msg = {}, {}
                    status_code = response_json['responseCode']
                    context().logger.error("get_applications function failed, status code: %s , error details: %s",
                                           status_code, response_json)
                    error_msg['message'] = "get_applications function failed"
                    if response_json.get('responseErrorDetails'):
                        error_msg['message'] = response_json['responseErrorDetails']
                    ErrorResponder.fill_error(return_obj, json.dumps(error_msg).encode(), status_code)
                    raise Exception(return_obj)
                results = results + response_json['assetListData']['asset']

            # check previous api call response hasMoreRecords
            if response_json and response_json['hasMore']:
                server_endpoint = asset_server_endpoint + '&lastSeenAssetId=%s' % (response_json['lastSeenAssetId'])
            else:
                pagination = False
        return results

    # Get all asset and vulnerability records
    def get_model_state_delta(self, last_model_state_id, new_model_state_id):

        last_model_state_id = epoch_to_datetime_conv(last_model_state_id)

        # fetch the recent changes
        host_list = self.get_assets(last_model_state_id)

        vuln_list = self.get_vulnerabilities()
        applications = self.get_applications(last_model_state_id)
        return append_vuln_in_asset(host_list, vuln_list, applications)
