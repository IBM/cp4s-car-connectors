import re
import ipaddress
import os
import datetime
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

def context_patch(incremental=True):


    context_args = {
        'car_service_apikey_url': 'https://example.com/api/car/v2',
        'api_key': None,
        'api_password': 'abc-xyz',
        'api_token': None,
        'car_service_token_url': None,
        'source': 'Microsoft-Windows-Defender-ATP',
        'debug': False,
        'last_model_state_id': "1568023215000",
        'new_model_state_id':  "1580649321920",
        'tenantID': 'account-123',
        'clientID': 'xyz123',
        'clientSecret': 'abcxyz',
        'vuln': None,
        'alerts': None,
        'export_data_dir': './cache/tmp',
        'export_data_page_size': 200,
        'connector_name': "test-connector-name",
    }
    Context(Struct(context_args))

    context().asset_server = AssetServer()
    context().data_collector = DataCollector()
    context().full_importer = FullImport()
    context().inc_importer = IncrementalImport()

    context().last_model_state_id = context().args.last_model_state_id
    context().new_model_state_id = context().args.new_model_state_id

    if not incremental:
        context().full_importer.create_source_report_object()



class JsonResponse:
    """
     Summary conversion of json data to dictionary.
          """
    def __init__(self, response_code, filename):
        self.status_code = response_code
        self.filename = filename

    # def status_code(self):
    #     return self.status_code

    def json(self):
        cur_path = os.path.dirname(__file__)
        abs_file_path = os.path.join(cur_path, "msatp_test_log", self.filename)
        json_file = open(abs_file_path)
        json_str = json_file.read()
        json_data = json.loads(json_str)
        return json_data

    def text(self):
        cur_path = os.path.dirname(__file__)
        abs_file_path = os.path.join(cur_path, "msatp_test_log", self.filename)
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

    # def status_code(self):
    #     return self.status_code

    # def text(self):
    #     return self.text


class Common:

    @staticmethod
    def ip_validate(ip_address):
        if ipaddress.ip_network(ip_address):
            is_valid_ip = True
        else:
            is_valid_ip = False
        return is_valid_ip

    @staticmethod
    def timestamp_validate(timestamp):
        is_valid_time = False
        if isinstance(timestamp, int):
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
    def asset_validate(asset_consumer):
        is_valid = False
        is_valid_asset = []
        for item in asset_consumer:
            is_valid_id = isinstance(item['external_id'], str)
            assert item['external_id'] is not None
            is_valid_asset.append(is_valid_id)
        if all(is_valid_asset):
            is_valid = True
        return is_valid

    @staticmethod
    def host_validate(hostname_consumer):
        is_valid = False
        is_valid_host = []
        assert hostname_consumer is not None
        for item in hostname_consumer:
            assert item['_key'] is not None
            is_valid_host.append(True)
            if all(is_valid_host):
                is_valid = True
        return is_valid

    @staticmethod
    def asset_host_validate(asset_hostname_consumer):
        is_valid = False
        is_valid_time_list = []
        is_valid_id_list = []
        assert asset_hostname_consumer is not None
        for item in asset_hostname_consumer:
            is_valid_id = isinstance(item['_from_external_id'], str)
            assert item['_from_external_id'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            is_valid_id_list.append(is_valid_id)
        if all([is_valid_id_list,is_valid_time_list]):
            is_valid = True
        return is_valid

    @staticmethod
    def ipaddr_validate(ipaddress_consumer):
        is_valid = False
        is_valid_ip = []
        for item in ipaddress_consumer:
            assert isinstance(item['_key'],str)
            assert item['_key'] is not None
            is_valid_ip.append(True)
        if all(is_valid_ip):
            is_valid = True
        return is_valid

    @staticmethod
    def mac_validate(mac_consumer):
        is_valid = False
        is_valid_mac = []
        assert mac_consumer is not None
        for item in mac_consumer:
            assert item['_key'] is not None
            is_valid = Common.mac_validate(item['_key'])
            is_valid_mac.append(True)
            if all(is_valid_mac):
                is_valid = True
        return is_valid

    @staticmethod
    def ip_mac_address_validate(ip_mac_consumer):
        is_valid = False
        is_valid_time_list = []
        assert ip_mac_consumer is not None
        for item in ip_mac_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        if all([is_valid_time_list]):
            is_valid = True
        return is_valid

    @staticmethod
    def asset_ip_validate(asset_ipaddress_consumer):
        is_valid = False
        is_valid_time_list = []
        assert asset_ipaddress_consumer is not None
        for item in asset_ipaddress_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        if all([is_valid_time_list]):
            is_valid = True
        return is_valid

    @staticmethod
    def asset_mac_validate(asset_mac_consumer):
        is_valid = False
        is_valid_time_list = []
        assert asset_mac_consumer is not None
        for item in asset_mac_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        if all([is_valid_time_list]):
            is_valid = True
        return is_valid

    @staticmethod
    def vuln_validate(vuln_consumer):
        is_valid = False
        # is_valid_vuln = []
        is_valid_ptime = []
        for item in vuln_consumer:
            assert isinstance(item['external_id'],str)
            assert item['external_id'] is not None
            # is_valid_disclosed = Common.date_string_validate(item['disclosed_on'])
            is_valid_published = Common.date_string_validate(item['published_on'])
            # is_valid_dtime.append(is_valid_disclosed)
            is_valid_ptime.append(is_valid_published)
        if all([is_valid_ptime]):
            is_valid = True
        return is_valid

    @staticmethod
    def asset_vuln_validate(asset_vuln_consumer):
        is_valid = False
        is_valid_time_list = []
        assert asset_vuln_consumer is not None
        for item in asset_vuln_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        if all([is_valid_time_list]):
            is_valid = True
        return is_valid

    @staticmethod
    def user_validate(user_consumer):
        is_valid = False
        is_valid_user = []
        for item in user_consumer:
            assert isinstance(item['external_id'], str)
            assert item.get('_key') is None
            assert item['external_id'] is not None
            is_valid_user.append(True)
        if all(is_valid_user):
            is_valid = True
        return is_valid

    @staticmethod
    def account_validate(account_consumer):
        is_valid = False
        is_valid_account = []
        for item in account_consumer:
            assert isinstance(item['external_id'], str)
            assert item.get('_key') is None
            assert item['external_id'] is not None
            is_valid_account.append(True)
        if all(is_valid_account):
            is_valid = True
        return is_valid

    @staticmethod
    def asset_account_validate(asset_account_consumer):
        is_valid_time_list = list()
        assert asset_account_consumer is not None
        for item in asset_account_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        return all([is_valid_time_list])

    @staticmethod
    def account_host_validate(account_host_consumer):
        is_valid_time_list = list()
        assert account_host_consumer is not None
        for item in account_host_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        return all([is_valid_time_list])

    @staticmethod
    def user_account_validate(user_account_consumer):
        is_valid_time_list = list()
        assert user_account_consumer is not None
        for item in user_account_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        return all([is_valid_time_list])

    @staticmethod
    def application_validate(application_consumer):
        is_valid = False
        is_valid_application = []
        for item in application_consumer:
            is_valid_id = isinstance(item['external_id'], str)
            assert item['external_id'] is not None
            is_valid_application.append(is_valid_id)
        if all(is_valid_application):
            is_valid = True
        return is_valid


    @staticmethod
    def asset_application_validate(asset_application_consumer):
        is_valid = False
        is_valid_time_list = []
        is_valid_id_list = []
        assert asset_application_consumer is not None
        for item in asset_application_consumer:
            is_valid_id = isinstance(item['_from_external_id'], str)
            assert item['_from_external_id'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            is_valid_id_list.append(is_valid_id)
        if all([is_valid_id_list,is_valid_time_list]):
            is_valid = True
        return is_valid

    @staticmethod
    def application_vulnerability_validate(application_vulnerability_consumer):
        is_valid_time_list = list()
        assert application_vulnerability_consumer is not None
        for item in application_vulnerability_consumer:
            assert item['timestamp'] is not None
            is_valid_time = Common.timestamp_validate(item['timestamp'])
            is_valid_time_list.append(is_valid_time)
            assert item['active'] is True
        return all([is_valid_time_list])