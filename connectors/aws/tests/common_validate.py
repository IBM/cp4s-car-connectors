import re
import ipaddress
import datetime
import logging
import os
import json

from car_framework.context import Context, context
from connector.server_access import AssetServer
from connector.data_collector import DataCollector
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport

class Struct(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
               setattr(self, a, [Struct(x) if isinstance(x, dict) else x for x in b])
            else:
               setattr(self, a, Struct(b) if isinstance(b, dict) else b)

def context_patch():

    context_args = {
        'car_service_apikey_url': 'https://example.com/api/car/v2',
        'api_key': None,
        'api_password': 'abc-xyz',
        'api_token': None,
        'car_service_token_url': None,
        'source': 'AWS-TEST',
        'debug': False,
        'accountId': 'account-123',
        'clientID': 'xyz123',
        'clientSecret': 'abcxyz',
        'region': "us-east-1",
        'last_model_state_id': "1580649320000",
        'new_model_state_id':  "1580649321920",
        'connector_name': "test-connector-name",
        'version': "0.0.0",
        'export_data_dir': './cache/tmp',
        'export_data_page_size': 200
    }
    Context(Struct(context_args))

    context().asset_server = AssetServer()
    context().data_collector = DataCollector()
    context().full_importer = FullImport()
    context().inc_importer = IncrementalImport()

    context().last_model_state_id = context().args.last_model_state_id
    context().new_model_state_id = context().args.new_model_state_id

class JsonResponse:
    """
     Summary conversion of json data to dictionary.
          """
    def __init__(self, response_code, filename):
        self.status_code = response_code
        self.filename = filename

    def status_code(self):
        return self.status_code

    def json(self):
        cur_path = os.path.dirname(__file__)
        abs_file_path = os.path.join(cur_path, "aws_test_log", self.filename)
        json_file = open(abs_file_path)
        json_str = json_file.read()
        json_data = json.loads(json_str)
        return json_data

    def text(self):
        cur_path = os.path.dirname(__file__)
        abs_file_path = os.path.join(cur_path, "aws_test_log", self.filename)
        json_file = open(abs_file_path)
        json_str = json_file.read()
        return json_str


class MockJsonResponse:
    """
    Summary Json response handler
        """
    def __init__(self, response_code, obj):
        self.status_code = response_code
        self.text = str(obj)

    def json(self):
        json_data = json.loads(self.text)
        return json_data


class JsonTextResponse:
    """
    Summary Json text response handler
        """
    def __init__(self, response_code, obj):
        self.status_code = response_code
        self.text = str(obj)

    def status_code(self):
        return self.status_code

    def text(self):
        return self.text


class Common:

    @staticmethod
    def ip_validate(ip_address):
        is_valid_ip = False
        if ipaddress.ip_network(ip_address):
            is_valid_ip = True
        return is_valid_ip

    @staticmethod
    def timestamp_validate(timestamp):
        is_valid_time = False
        time_len = len(str(timestamp))
        if time_len == 13:
            is_valid_time = True
        return is_valid_time

    @staticmethod
    def mac_validate(mac_address):
        is_valid_mac = False
        if re.match("[0-9a-f]{2}([:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_address.lower()):
            is_valid_mac = True
        return is_valid_mac

    @staticmethod
    def date_string_validate(date_text):
        try:
            if len(date_text) >= 28:
                datetime.datetime.strptime(date_text[:26], '%Y-%m-%dT%H:%M:%S.%f')
            else:
                datetime.datetime.strptime(date_text, '%Y-%m-%dT%H:%M:%S.%fZ')
            is_valid_date = True
        except:
            is_valid_date = False
        return is_valid_date

class TestConsumer:

    @staticmethod
    def application_validate(app_consumer):
        is_valid_app = list()
        for item in app_consumer:
            assert item['external_id'] is not None
            is_valid_id = isinstance(item['external_id'], str)
            is_valid_app.append(is_valid_id)
        return all(is_valid_app)

    @staticmethod
    def account_validate(rpt_account_consumer):
        is_valid_user = list()
        assert rpt_account_consumer is not None
        for item in rpt_account_consumer:
            is_valid = isinstance(item['external_id'], str)
            assert item['external_id'] is not None
            is_valid_user.append(is_valid)
        return all(is_valid_user)
    
    @staticmethod
    def user_validate(rpt_user_consumer):
        is_valid_user = list()
        assert rpt_user_consumer is not None
        for item in rpt_user_consumer:
            is_valid = isinstance(item['external_id'], str)
            assert item['external_id'] is not None
            is_valid_user.append(is_valid)
        return all(is_valid_user)

    @staticmethod
    def host_validate(rpt_host_consumer):
        is_valid_host = list()
        assert rpt_host_consumer is not None
        for item in rpt_host_consumer:
            is_valid = isinstance(item['_key'], str)
            assert item['_key'] is not None
            is_valid_host.append(is_valid)
        return all(is_valid_host)

    @staticmethod
    def asset_validate(ast_consumer):
        is_valid_asset = list()
        for item in ast_consumer:
            assert item['external_id'] is not None
            is_valid_id = isinstance(item['external_id'], str)
            is_valid_asset.append(is_valid_id)
        return all(is_valid_asset)

    @staticmethod
    def ip_adr_validate(ip_consumer):
        is_valid_ip_list = []
        for item in ip_consumer:
            is_valid_ip = Common.ip_validate(item['_key'])
            is_valid_ip_list.append(is_valid_ip)
        return all(is_valid_ip_list)

    @staticmethod
    def mac_validate(mac_consumer):
        is_valid_mac = list()
        assert mac_consumer is not None
        for item in mac_consumer:
            assert item['_key'] is not None
            is_valid = Common.mac_validate(item['_key'])
            is_valid_mac.append(is_valid)
        return all(is_valid_mac)

    @staticmethod
    def vuln_validate(vul_consumer):
        is_valid_vuln, is_valid_time = list(), list()
        for item in vul_consumer:
            is_valid = isinstance(item['external_id'], str)
            is_valid_vuln.append(is_valid)
            publish_time = Common.date_string_validate(item['published_on'])
            disclose_time = Common.date_string_validate(item['disclosed_on'])
            is_valid_time.append(publish_time)
            is_valid_time.append(disclose_time)
        return all([is_valid_time, is_valid_vuln])

    @staticmethod
    def db_validate(db_consumer):
        is_valid_db_list = list()
        assert db_consumer is not None
        for item in db_consumer:
            assert item['external_id'] is not None
            is_valid_db = isinstance(item['external_id'], str)
            is_valid_db_list.append(is_valid_db)
        return all([is_valid_db_list])

    @staticmethod
    def container_validate(cnt_consumer):
        is_valid_cnt_list = list()
        assert cnt_consumer is not None
        for item in cnt_consumer:
            assert item['external_id'] is not None
            is_valid_cnt = isinstance(item['external_id'], str)
            is_valid_cnt_list.append(is_valid_cnt)
            assert item['image'] is not None
        return all([is_valid_cnt_list])

    @staticmethod
    def geolocation_validate(geolocation_consumer):
        is_valid_cnt_list = list()
        assert geolocation_consumer is not None
        for item in geolocation_consumer:
            assert item['external_id'] is not None
            is_valid_cnt = isinstance(item['external_id'], str)
            is_valid_cnt_list.append(is_valid_cnt)
            assert item['region'] is not None
        return all([is_valid_cnt_list])

    @staticmethod
    def edges_validate(edge_consumer):
        is_valid_time_list = list()
        assert edge_consumer is not None
        for item in edge_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        return all([is_valid_time_list])