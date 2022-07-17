from car_framework.context import context
from car_framework.data_handler import BaseDataHandler

ACTIVE = True
BASE_SCORE_MAP = {"high": 8, "medium": 5, "low": 2, "informational": 0}


class DataHandler(BaseDataHandler):

    def __init__(self):
        super().__init__()

    def create_source_report_object(self):
        if not (self.source and self.report):
            # create source and report entry and it is compuslory for each imports API call
            self.source = {'_key': context().args.source, 'name': context().args.tenantID, 'description': 'Microsoft Defender for Endpoint imports', 'product_link' : 'https://securitycenter.windows.com/'}
            self.report = {'_key': str(self.timestamp), 'timestamp' : self.timestamp, 'type': 'Microsoft Defender for Endpoint', 'description': 'Microsoft Defender for Endpoint imports'}

        return {'source': self.source, 'report': self.report}

    def handle_user(self, obj):
        user = dict()
        if obj.get('value'):
            obj=obj['value']
        user['external_id'] = obj['id']
        user['upn'] = obj['userPrincipalName']
        user['name'] = obj['displayName']
        user['email'] = obj['mail']
        user['given_name'] = obj['givenName']
        user['family_name'] = obj['surname']
        user['role'] = obj['jobTitle']
        user['department'] = obj['officeLocation']
        used_keys = ['id', 'userPrincipalName', 'displayName', 'mail', 'givenName', 'surname', 'jobTitle','officeLocation']
        keys = [k for k in obj.keys() if k not in used_keys]
        # for k in keys:
        #     user[k] = obj[k]
        self.add_collection('user', user, 'external_id')

    def handle_account(self, obj):
        account = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('id') and obj['id']:
            account['external_id'] = obj['id']
            account['name'] = obj['displayName'] if obj['displayName'] else obj['userPrincipalName']
            if obj.get('manager_id'):
                account['manager_id'] = obj['manager_id']
            self.add_collection('account', account, 'external_id')

    def handle_user_account(self, obj):
        user_account = dict()
        if obj.get('value'):
            obj=obj['value']
        user_account['_from_external_id'] = obj['id']
        user_account['_to_external_id'] = obj['id']
        self.add_edge('user_account', user_account)

    def handle_group(self, obj):
        group = dict()
        if obj.get('value'):
            obj=obj['value']
        group['external_id'] = obj['id']
        group['description'] = obj['description']
        group['name'] = obj['displayName']
        group['created_date_time'] = obj['createdDateTime']
        group['deleted_date_time'] = obj['deletedDateTime']
        group['expiration_date_time'] = obj['expirationDateTime']
        group['renewed_date_time'] = obj['renewedDateTime']
        group['classification'] = obj['classification']
        self.add_collection('group', group, 'external_id')

    def handle_account_group(self, obj):
        user_group = dict()
        if obj.get('value'):
            obj=obj['value']
        user_group['_from_external_id'] = obj['user_id']
        user_group['_to_external_id'] = obj['group_id']
        self.add_edge('account_group', user_group)

    def handle_approle(self, obj):
        approle = dict()
        if obj.get('value'):
            obj=obj['value']
        approle['external_id'] = obj['id']
        approle['app_role_id'] = obj['appRoleId']
        approle['principal_id'] = obj['principalId']
        approle['principal_name'] = obj['principalDisplayName']
        approle['principal_type'] = obj['principalType']
        approle['resource_display_name '] = obj['resourceDisplayName']
        approle['resource_id'] = obj['resourceId']
        self.add_collection('approle', approle, 'external_id')

    def handle_account_approle(self, obj):
        user_approle = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('type') and obj['type'] == 'user':
            user_approle['_from_external_id'] = obj['user_id']
            user_approle['_to_external_id'] = obj['id']
            self.add_edge('account_approle', user_approle)

    def handle_group_approle(self, obj):
        group_approle = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('type') and obj['type']=='group':
            group_approle['_from_external_id'] = obj['group_id']
            group_approle['_to_external_id'] = obj['id']
            self.add_edge('group_approle', group_approle)

    def handle_permissiongrants(self, obj):
        permissiongrants = dict()
        if obj.get('value'):
            obj=obj['value']
        print(obj)
        permissiongrants['external_id'] = obj['id']
        permissiongrants['client_id'] = obj['clientId']
        permissiongrants['client_app_id'] = obj['clientAppId']
        permissiongrants['resource_app_id'] = obj['resourceAppId']
        permissiongrants['permission_type'] = obj['permissionType']
        permissiongrants['permission'] = obj['permission']
        permissiongrants['resource_display_name '] = obj['resourceDisplayName']
        self.add_collection('permissiongrants', permissiongrants, 'external_id')
        
    def handle_group_permissiongrants(self, obj):
        group_permissiongrants = dict()
        if obj.get('value'):
            obj=obj['value']
        group_permissiongrants['_from_external_id'] = obj['group_id']
        group_permissiongrants['_to_external_id'] = obj['permissiongrants_id']
        self.add_edge('group_permissiongrants', group_approle)

    def handle_application(self, obj):
        application = dict()
        if obj.get('value'):
            obj = obj['value']
        if obj.get('appId') and obj['appId']:
            application['external_id'] = obj['appId']
            application['name'] = obj['appDisplayName'] if obj['appDisplayName'] else 'None'
            self.add_collection('application', application, 'external_id')

    def handle_ipaddress(self, obj):
        ipaddress = dict()
        if obj.get('value'):
            obj = obj['value']
        if obj.get('ipAddress'):
            ipaddress['_key'] = obj['ipAddress']
            self.add_collection('ipaddress', ipaddress, '_key')

    def handle_asset(self, obj):
        asset = dict()
        if obj.get('value'):
            obj = obj['value']
        if obj.get('deviceDetail') and isinstance(obj['deviceDetail'], dict) and obj['deviceDetail']['deviceId']:
            obj = obj['deviceDetail']
            asset['external_id'] = obj['deviceId']
            asset['name'] = obj['displayName']
            asset['type'] = obj['operatingSystem']
            asset['is_compliant'] = obj['isCompliant']
            asset['is_managed'] = obj['isManaged']
            asset['trust_type'] = obj['trustType']
            self.add_collection('asset', asset, 'external_id')

    def handle_browser(self, obj):
        browser = dict()
        if obj.get('value'):
            obj = obj['value']
        if obj.get('deviceDetail') and isinstance(obj['deviceDetail'], dict) and obj['deviceDetail']['browser']:
            obj = obj['deviceDetail']
            browser['external_id'] = obj['browser']
            browser['browser'] = obj['browser']
            self.add_collection('browser', browser, 'external_id')

    def handle_geolocation(self, obj):
        geolocation = dict()
        if obj.get('value'):
            obj = obj['value']
        if obj.get('location') and isinstance(obj['location'], dict):
            geolocation['external_id'] = obj['id']
            obj = obj['location']
            geolocation['region'] = obj['countryOrRegion']
            if obj.get('state') and obj.get('city') and obj['state'] and obj['city']:
                geolocation['description'] = f'{obj["state"]}, {obj["city"]}'
            if obj.get('geoCoordinates') and isinstance(obj['geoCoordinates'], dict):
                geolocation['latitude'] = obj['geoCoordinates']['latitude']
                geolocation['longitude'] = obj['geoCoordinates']['longitude']
            self.add_collection('geolocation', geolocation, 'external_id')

    def handle_signin(self, obj):
        signin = dict()
        if obj.get('value'):
            obj = obj['value']
        signin['external_id'] = obj['id']
        signin['client_app_used'] = obj['clientAppUsed']
        signin['created_time'] = obj['createdDateTime']
        signin['is_interactive'] = obj['isInteractive']
        signin['risk_detail'] = obj['riskDetail']
        signin['risk_level_aggregated'] = obj['riskLevelAggregated']
        signin['risk_level_during_signin '] = obj['riskLevelDuringSignIn']
        signin['risk_state'] = obj['riskState']
        if len(obj['riskEventTypes'])>0:
            signin['risk_types'] = str(obj['riskEventTypes'])
        self.add_collection('signin', signin, 'external_id')

    def handle_account_application(self, obj):
        account_application = dict()
        if obj.get('value'):
            obj=obj['value']
        account_application['_from_external_id'] = obj['userId']
        account_application['_to_external_id'] = obj['appId']
        self.add_edge('account_application', account_application)

    def handle_account_ipaddress(self, obj):
        account_ipaddress = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('userId') and obj.get('ipAddress'):
            account_ipaddress['_from_external_id'] = obj['userId']
            account_ipaddress['_to'] = 'ipaddress/' + obj['ipAddress']
            self.add_edge('account_ipaddress', account_ipaddress)

    def handle_asset_account(self, obj):
        asset_account = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('deviceDetail') and isinstance(obj['deviceDetail'], dict) and obj['deviceDetail']['deviceId']:
            asset_account['_from_external_id'] = obj['deviceDetail']['deviceId']
            asset_account['_to_external_id'] = obj['userId']
            self.add_edge('asset_account', asset_account)

    def handle_browser_account(self, obj):
        browser_account = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('deviceDetail') and isinstance(obj['deviceDetail'], dict) and obj['deviceDetail']['browser']:
            browser_account['_from_external_id'] = obj['deviceDetail']['browser']
            browser_account['_to_external_id'] = obj['userId']
            self.add_edge('browser_account', browser_account)

    def handle_asset_application(self, obj):
        asset_application = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('deviceDetail') and isinstance(obj['deviceDetail'], dict) and obj['deviceDetail']['deviceId']:
            asset_application['_from_external_id'] = obj['deviceDetail']['deviceId']
            asset_application['_to_external_id'] = obj['appId']
            self.add_edge('asset_application', asset_application)

    def handle_application_ipaddress(self, obj):
        application_ipaddress = dict()
        if obj.get('value'):
            obj=obj['value']
        application_ipaddress['_from_external_id'] = obj['appId']
        application_ipaddress['_to'] = 'ipaddress/' + obj['ipAddress']
        self.add_edge('application_ipaddress', application_ipaddress)

    def handle_asset_geolocation(self, obj):
        asset_geolocation = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('deviceDetail') and isinstance(obj['deviceDetail'], dict) and obj['deviceDetail']['deviceId']:
            asset_geolocation['_from_external_id'] = obj['deviceDetail']['deviceId']
            asset_geolocation['_to_external_id'] = obj['id']
            self.add_edge('asset_geolocation', asset_geolocation)

    def handle_signin_application(self, obj):
        signin_application = dict()
        if obj.get('value'):
            obj=obj['value']
        signin_application['_from_external_id'] = obj['id']
        signin_application['_to_external_id'] = obj['appId']
        self.add_edge('signin_application', signin_application)

    def handle_signin_ipaddress(self, obj):
        signin_ipaddress = dict()
        if obj.get('value'):
            obj=obj['value']
        signin_ipaddress['_from_external_id'] = obj['id']
        signin_ipaddress['_to'] = 'ipaddress/' + obj['ipAddress']
        self.add_edge('signin_ipaddress', signin_ipaddress)

    def handle_signin_approle(self, obj):
        signin_approle = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj['resourceId']:
            signin_approle['_from_external_id'] = obj['id']
            signin_approle['_to_external_id'] = obj['resourceId']
            self.add_edge('signin_approle', signin_approle)
        
    def handle_signin_asset(self, obj):
        signin_asset = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj.get('deviceDetail') and isinstance(obj['deviceDetail'], dict) and obj['deviceDetail']['deviceId']:
            signin_asset['_from_external_id'] = obj['id']
            signin_asset['_to_external_id'] = obj['deviceDetail']['deviceId']
            self.add_edge('signin_asset', signin_asset)

    def handle_signin_geolocation(self, obj):
        signin_geolocation = dict()
        if obj.get('value'):
            obj=obj['value']
        signin_geolocation['_from_external_id'] = obj['id']
        signin_geolocation['_to_external_id'] = obj['id']
        self.add_edge('signin_geolocation', signin_geolocation)

    def handle_account_signin(self, obj):
        account_signin = dict()
        if obj.get('value'):
            obj=obj['value']
        account_signin['_from_external_id'] = obj['userId']
        account_signin['_to_external_id'] = obj['id']
        self.add_edge('account_signin', account_signin)
        
    def handle_account_from_signin(self, obj):
        account = dict()
        if obj.get('value'):
            obj=obj['value']
        account['external_id'] = obj['userId']
        account['name'] = obj['userDisplayName']
        self.add_collection('account', account, 'external_id')

    def handle_approle_from_signin(self, obj):
        approle = dict()
        if obj.get('value'):
            obj=obj['value']
        if obj['resourceId']:
            approle['external_id'] = obj['resourceId']
            approle['app_role_id'] = obj['resourceId']
            approle['principal_name'] = obj['resourceDisplayName']
            self.add_collection('approle', approle, 'external_id')

    def handle_audit(self, obj):
        audit = dict()
        if obj.get('value'):
            obj = obj['value']
        audit['external_id'] = obj['id']
        audit['category'] = obj['category']
        audit['result'] = obj['result']
        audit['result_reason'] = obj['resultReason']
        audit['name'] = obj['activityDisplayName']
        audit['logged_by'] = obj['loggedByService']
        audit['additional_details'] = str(obj['additionalDetails']) if obj['additionalDetails'] else ''
        self.add_collection('audit', audit, 'external_id')
        
    def handle_account_from_audits(self, obj):
        if obj.get('value'):
            obj = obj['value']
        if obj.get('account'):
            for acc in obj['account']:
                self.handle_account(acc)
    
    def handle_group_from_audits(self, obj):
        if obj.get('value'):
            obj = obj['value']
        if obj.get('group'):
            for gr in obj['group']:
                group = dict()
                group['external_id'] = gr['id']
                group['name'] = gr['displayName']
                self.add_collection('group', group, 'external_id')
                
    def handle_application_from_audits(self, obj):
        if obj.get('value'):
            obj = obj['value']
        if obj.get('app'):
            for app in obj['app']:
                application = dict()
                application['appId'] = app['id'] if app.get('id') else app['appId']
                application['appDisplayName'] = app['displayName']
                self.handle_application(application)

    def handle_audit_account(self, obj):
        if obj.get('value'):
            obj=obj['value']
        if obj.get('account'):
            for acc in obj['account']:
                if acc.get('id') and acc['id']:
                    audit_account = dict()
                    audit_account['_from_external_id'] = obj['id']
                    audit_account['_to_external_id'] = acc['id']
                    audit_account['type'] = acc['interaction_type']
                    self.add_edge('audit_account', audit_account)

    def handle_audit_group(self, obj):
        if obj.get('value'):
            obj=obj['value']
        if obj.get('group'):
            for group in obj['group']:
                if group.get('id') and group['id']:
                    audit_group = dict()
                    audit_group['_from_external_id'] = obj['id']
                    audit_group['_to_external_id'] = group['id']
                    audit_group['type'] = group['interaction_type']
                    self.add_edge('audit_group', audit_group)

    def handle_audit_application(self, obj):
        if obj.get('value'):
            obj=obj['value']
        if obj.get('app'):
            for app in obj['app']:
                if app.get('id') and app['id']:
                    audit_application = dict()
                    audit_application['_from_external_id'] = obj['id']
                    audit_application['_to_external_id'] = app['id']
                    audit_application['type'] = app['interaction_type']
                    self.add_edge('audit_application', audit_application)
                
