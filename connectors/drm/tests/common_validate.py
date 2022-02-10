import re
import ipaddress
import datetime
import logging
import os
import json
from unittest.mock import patch, Mock

from requests import auth
from requests_toolbelt import MultipartEncoder

from car_framework.context import Context, context
from connector.server_access import DRMServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from connector.data_handler import DataHandler


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
        'source': 'DRM-TEST',
        'debug': False,
        'pageSize': 500,
        'region': "us-east-1",
        'username':'admin',
        'password': '123',
        'last_model_state_id': "1580649320000",
        'new_model_state_id': "1580649321920",
        'tenantUrl': 'https://test/drm/albatross',
        'tenant_bearer_token_url' : '/user/login',
        'drm_endpoint_url' : 'https://test/car/',
        'drm_server_endpoint' : "https://test",
        'connector_name': "test-connector-name",
    }

    Context(Struct(context_args))
    context().drm_server = DRMServer()
    context().data_handler= DataHandler('xrefproperties')
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
        abs_file_path = os.path.join(cur_path, "DRM-data", self.filename)
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
        assert app_consumer['external_id'] is not None
        is_valid_id = isinstance(app_consumer['external_id'], str)
        assert app_consumer['external_id'] is not None
        is_valid_app.append(is_valid_id)
        return all(is_valid_app)

    @staticmethod
    def businessprocess_validate(businessprocess_consumer):
        is_valid_businessprocess = list()
        assert businessprocess_consumer is not None
        is_valid = isinstance(businessprocess_consumer['external_id'], str)
        assert businessprocess_consumer['external_id'] is not None
        is_valid_businessprocess.append(is_valid)
        return all(is_valid_businessprocess)

    @staticmethod
    def ip_adr_validate(ip_consumer):
        is_valid_ip_list = list()
        for item in ip_consumer:
            is_valid_ip = isinstance(ip_consumer['_key'],str)
            is_valid_ip_list.append(is_valid_ip)
        return all(is_valid_ip_list)

    @staticmethod
    def businessprocess_application_validate(businessprocess_application_consumer):
        is_valid_businessprocess_application = list()
        assert businessprocess_application_consumer is not None
        is_valid = isinstance(businessprocess_application_consumer['external_id'], str)
        assert businessprocess_application_consumer['external_id'] is not None
        assert businessprocess_application_consumer['_from_external_id'] is not None
        assert businessprocess_application_consumer['_to_external_id'] is not None
        is_valid_businessprocess_application.append(is_valid)
        return all(is_valid_businessprocess_application)

    @staticmethod
    def ipaddress_application_validate(ipaddress_application_consumer):
        is_valid_ipaddreess_application = list()
        assert ipaddress_application_consumer is not None
        is_valid = isinstance(ipaddress_application_consumer['_from_external_id'], str)
        assert ipaddress_application_consumer['_from_external_id'] is not None
        assert ipaddress_application_consumer['_to'] is not None
        is_valid_ipaddreess_application.append(is_valid)
        return all(is_valid_ipaddreess_application)

    @staticmethod
    def update_application_validate(self,app_consumer):
        is_valid_app = list()
        assert app_consumer['external_id'] is not None
        is_valid_id = isinstance(app_consumer['external_id'], str)
        is_valid_name= isinstance(app_consumer['description'],str)
        assert app_consumer['description'] is not None
        self.assertEqual(app_consumer['description'], 'Adept Payroll update')
        is_valid_app.append(is_valid_id)
        is_valid_app.append(is_valid_name)
        return all(is_valid_app)

    @staticmethod
    def update_businessprocess_validate(self, businessprocess_consumer):
        is_valid_app = list()
        assert businessprocess_consumer['external_id'] is not None
        is_valid_id = isinstance(businessprocess_consumer['external_id'], str)
        is_valid_name = isinstance(businessprocess_consumer['description'], str)
        assert businessprocess_consumer['description'] is not None
        self.assertEqual(businessprocess_consumer['description'], 'Claims Benefits and Payments update')
        is_valid_app.append(is_valid_id)
        is_valid_app.append(is_valid_name)
        return all(is_valid_app)

    @staticmethod
    def update_ipaddress_validate(self, ipaddress_consumer):
        is_valid_app = list()
        assert ipaddress_consumer['_key'] is not None
        is_valid_id = isinstance(ipaddress_consumer['_key'], str)
        is_valid_name = isinstance(ipaddress_consumer['description'], str)
        assert ipaddress_consumer['description'] is not None
        self.assertEqual(ipaddress_consumer['description'], '1001_mysql_pubs_Guardium_new')
        is_valid_app.append(is_valid_id)
        is_valid_app.append(is_valid_name)
        return all(is_valid_app)

    @staticmethod
    def get_collection_validate(collection_consumer):
        is_valid_collection = list()
        assert collection_consumer is not None
        for item in collection_consumer:
            is_valid = isinstance(item['id'], str)
            assert item['id'] is not None
        is_valid_collection.append(is_valid)
        return all(is_valid_collection)

    @staticmethod
    def get_deleted_collection_validate(self,delete_collection_consumer):
        is_valid_delete_collection = list()
        assert delete_collection_consumer is not None
        for item in delete_collection_consumer:
            self.assertEqual(item['isDeleted'], 1)
            is_valid_id = isinstance(item['id'], str)
            check_delete = isinstance(item['isDeleted'], int)
            assert item['id'] is not None
        is_valid_delete_collection.append(is_valid_id)
        is_valid_delete_collection.append(check_delete)
        return all(is_valid_delete_collection)

    @staticmethod
    def deleted_application_validate(self,app_consumer):
        is_valid_app = list()
        assert app_consumer['external_id'] is not None
        is_valid_id = isinstance(app_consumer['external_id'], str)
        self.assertIsNotNone(app_consumer['_deleted'])
        is_valid_delete = isinstance(app_consumer['_deleted'], int)
        is_valid_app.append(is_valid_id)
        is_valid_app.append(is_valid_delete)

        return all(is_valid_app)

    @staticmethod
    def deleted_businessprocess_validate(self, businessprocess_consumer):
        is_valid_app = list()
        assert businessprocess_consumer['external_id'] is not None
        is_valid_id = isinstance(businessprocess_consumer['external_id'], str)
        self.assertIsNotNone(businessprocess_consumer['_deleted'])
        is_valid_delete = isinstance(businessprocess_consumer['_deleted'], int)
        is_valid_app.append(is_valid_id)
        is_valid_app.append(is_valid_delete)

        return all(is_valid_app)

    @staticmethod
    def deleted_ipaddress_validate(self, ipaddreess_consumer):
        is_valid_ip = list()
        assert ipaddreess_consumer['_key'] is not None
        is_valid_ipaddr = isinstance(ipaddreess_consumer['_key'], str)
        self.assertIsNotNone(ipaddreess_consumer['_deleted'])
        is_valid_delete = isinstance(ipaddreess_consumer['_deleted'], int)
        is_valid_ip.append(is_valid_ipaddr)
        is_valid_ip.append(is_valid_delete)

        return all(is_valid_ip)



