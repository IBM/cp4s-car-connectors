from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

ACTIVE = True
BASE_SCORE_MAP = {"high": 8, "medium": 5, "low": 2, "informational": 0}


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()
        self.params = {'browser': ['browser']}
    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry and it is compuslory for each imports API call
            self.source = {'_key': context().args.source, 'name': 'Verify Trust', 'description': 'Verify Trust', 'product_link' : ''}
            self.report = {'_key': str(self.timestamp), 'timestamp' : self.timestamp, 'type': 'Verify Trust', 'description': 'Verify Trust'}

        return {'source': self.source, 'report': self.report}


    def handle_ipaddress(self, obj):
        if obj.get('device_data') and obj['device_data'].get('network'):
            ipaddress = dict()
            data = obj['device_data']['network']
            if data.get('remote_addr'): 
                ipaddress['_key'] = data['remote_addr']
                ipaddress['name'] = data['remote_addr']
            if data['ip_class']: ipaddress['ip_class'] = data['ip_class']
            if data['ip_time_zone']: ipaddress['ip_time_zone'] = data['ip_time_zone']
            if data['isp']: ipaddress['isp'] = data['isp']
            if data['org']: ipaddress['org'] = data['org']
            if data['x_forwarded_for']: ipaddress['x_forwarded_for'] = data['x_forwarded_for']
            self.add_collection('ipaddress', ipaddress, '_key')

    def handle_browser(self, obj):
        browser = dict()
        if obj.get('device_data') and obj['device_data'].get('browser'):
            browser['external_id'] = obj['permanent_user_id']
            browser['user_id'] = obj['permanent_user_id']
            temp_data = obj['device_data']['browser']
            if temp_data['browser']: browser['browser'] = temp_data['browser']
            if temp_data['browser_version']: browser['browser_version'] = temp_data['browser_version']
            if temp_data['client_language']: browser['client_language'] = temp_data['client_language']
            if temp_data['client_time_zone']: browser['client_time_zone'] = temp_data['client_time_zone']
            if temp_data['user_agent']: browser['user_agent'] = temp_data['user_agent']
        if obj.get('device_data') and obj['device_data'].get('device_attributes'):
            temp_data = obj['device_data']['device_attributes']
            if temp_data['agent_key']: browser['agent_key'] = temp_data['agent_key']
            if temp_data['cpu']: browser['cpu'] = temp_data['cpu']
            if temp_data['digest']: browser['digest'] = temp_data['digest']
            if temp_data['machine_id']: browser['machine_id'] = temp_data['machine_id'] 
            if temp_data['os']: browser['os'] = temp_data['os']
            if temp_data['platform']: browser['platform'] = temp_data['platform']
            if temp_data['screen_dpi']: browser['screen_dpi'] = temp_data['screen_dpi']
            if temp_data['screen_height']: browser['screen_height'] = temp_data['screen_height']
            if temp_data['screen_touch']: browser['screen_touch'] = temp_data['screen_touch']
            if temp_data['screen_width']: browser['screen_width'] = temp_data['screen_width']
        if obj.get('device_data') and obj['device_data'].get('mobile_attributes'):
            temp_data = obj['device_data']['mobile_attributes']
            if temp_data['cpu_type']: browser['mobile_cpu_type'] = temp_data['cpu_type']
            if temp_data['device_language']: browser['mobile_device_language'] = temp_data['device_language']
            if temp_data['device_type']: browser['mobile_device_type'] = temp_data['device_type']
            if temp_data['line_carrier']: browser['mobile_line_carrier'] = temp_data['line_carrier']
            if temp_data['mrst_app_count']: browser['mobile_mrst_app_count'] = temp_data['mrst_app_count']
            if temp_data['number_of_installed_applications']: browser['mobile_number_of_installed_applications'] = temp_data['number_of_installed_applications']
            if temp_data['os_version']: browser['mobile_os_version'] = temp_data['os_version']
            if temp_data['root_hiders']: browser['mobile_root_hiders'] = temp_data['root_hiders']
            if temp_data.get('sim_data'):
                if temp_data['sim_data']['iccid']: browser['sim_data_iccid'] = temp_data['sim_data']['iccid']
                if temp_data['sim_data']['imsi']: browser['sim_data_imsi'] = temp_data['sim_data']['imsi']
            if temp_data['time_zone']: browser['mobile_time_zone'] = temp_data['time_zone']
            if temp_data['wifi_mac_address']: browser['wifi_mac_address'] = temp_data['wifi_mac_address']
            if temp_data['wifi_ssid']: browser['wifi_ssid'] = temp_data['wifi_ssid']
        if obj.get('third_party_intelligence') and obj['third_party_intelligence'].get('carrier_analytics'):
            temp_data = obj['third_party_intelligence']['carrier_analytics']
            if temp_data['carrier_name']: browser['carrier_name'] = temp_data['carrier_name']
            if temp_data['contact_city']:  browser['contact_city'] = temp_data['contact_city']
        if len(browser)>0:
            self.add_collection('browser', browser, 'external_id')


    def handle_account_ipaddress(self, obj):
        if obj.get('device_data') and obj['device_data'].get('network') and obj.get('permanent_user_id'):
            account_ipaddress = dict()
            account_ipaddress['_from_external_id'] = obj["permanent_user_id"]
            account_ipaddress['_to'] = 'ipaddress/' + obj['device_data']['network']['remote_addr']
            self.add_edge('account_ipaddress', account_ipaddress)

    def handle_user(self, obj):
        user = dict()
        if obj.get('permanent_user_id'):
            user['external_id'] = obj['permanent_user_id']
            user['username'] = obj['permanent_user_id']
            if obj.get('user_data') and obj['user_data'].get('encrypted_user_id') and obj['user_data'].get('encryption_key_id'):
                if obj['user_data']['encrypted_user_id']: user['id'] = obj['user_data']['encrypted_user_id']
                if obj['user_data']['encryption_key_id']: user['key_id'] = obj['user_data']['encryption_key_id']
            if obj.get('third_party_intelligence') and obj['third_party_intelligence'].get('carrier_analytics'):
                if obj['third_party_intelligence']['carrier_analytics']['contact_first_name']: user['given_name'] = obj['third_party_intelligence']['carrier_analytics']['contact_first_name']
                if obj['third_party_intelligence']['carrier_analytics']['contact_last_name']: user['family_name'] = obj['third_party_intelligence']['carrier_analytics']['contact_last_name']
            self.add_collection('user', user, 'external_id')

    def handle_account(self, obj):
        account = dict()
        if obj.get('permanent_user_id'):
            account['external_id'] = obj['permanent_user_id']
            account['name'] = obj['permanent_user_id']
            if obj.get('user_data') and obj['user_data'].get('encrypted_user_id'):
                if obj['user_data']['encrypted_user_id']: account['id'] = obj['user_data']['encrypted_user_id']
            self.add_collection('account', account, 'external_id')

    def handle_risk(self, obj):
        risk = dict()
        if obj.get('pinpoint_assessment') and obj['pinpoint_assessment'].get('risk'):
            temp_data = obj['pinpoint_assessment']['risk']
            risk['external_id'] = temp_data['reason_id']
            risk['id'] = temp_data['reason_id']
            risk['name'] = temp_data['reason_id']
            risk['description'] = temp_data['reason']
            risk['risk_score'] = temp_data['risk_score']
            risk['recommendation'] = temp_data['recommendation']
            if obj['pinpoint_assessment'].get('bot_detection'):
                temp_data = obj['pinpoint_assessment']['bot_detection']
                risk['is_bot'] = temp_data['is_bot']
                risk['bot_label'] = temp_data['bot_label']
                risk['bot_score'] = temp_data['bot_score']
            if obj['pinpoint_assessment'].get('device_intelligence'):
                risk['risky_device'] = obj['pinpoint_assessment']['device_intelligence']['risky_device']
            if obj['pinpoint_assessment'].get('network_intelligence'):
                risk['risky_connection'] = obj['pinpoint_assessment']['network_intelligence']['risky_connection']
            print(f'risk: {risk}')
            self.add_collection('risk', risk, 'external_id')

    def handle_risk_ipaddress(self, obj):
        risk_ipaddress = dict()
        if obj.get('risk') and obj['device_data']['network'].get('remote_addr'):
            risk_ipaddress['_from_external_id'] = obj['pinpoint_assessment']['risk']['reason_id']
            risk_ipaddress['_to_external_id'] = 'ipaddress/' + obj['device_data']['network']['remote_addr']
            self.add_edge('risk_ipaddress', risk_ipaddress)
    
    def handle_user_account(self, obj):
        user_account = dict()
        if obj.get('permanent_user_id'):
            user_account['_from_external_id'] = obj['permanent_user_id']
            user_account['_to_external_id'] = obj['permanent_user_id']
            self.add_edge('user_account', user_account)
    
    def handle_browser_account(self, obj):
        browser_account = dict()
        if obj.get('permanent_user_id') and obj.get('device_data') and obj['device_data'].get('browser'):
            browser_account['_from_external_id'] = obj['device_data']['browser']['browser']
            browser_account['_to_external_id'] = obj['permanent_user_id']
            self.add_edge('browser_account', browser_account)

    
    def handle_browser_ipaddress(self, obj):
        browser_ipaddress = dict()
        if obj.get('permanent_user_id') and obj.get('device_data') and obj['device_data'].get('browser') and obj['device_data']['network'].get('remote_addr'):
            browser_ipaddress['_from_external_id'] = obj['device_data']['browser']['browser']
            browser_ipaddress['_to'] = 'ipaddress/' + obj['device_data']['network']['remote_addr']
            self.add_edge('browser_ipaddress', browser_ipaddress)
            

