import re

from car_framework.context import context
from car_framework.util import DatasourceFailure
from connector.data_handler import epoch_to_datetime_conv, deep_get
from falconpy import Discover
from falconpy import SpotlightVulnerabilities


# Page limits
DISCOVER_PAGE_SIZE = 100
SPOTLIGHT_PAGE_SIZE = 5000


class AssetServer:

    def __init__(self):
        self.base_url = "https://" + context().args.CONNECTION_HOST
        self.client_id = context().args.CONFIGURATION_AUTH_CLIENT_ID
        self.client_secret = context().args.CONFIGURATION_AUTH_CLIENT_SECRET

    def test_connection(self):
        """test the connection"""
        try:
            discover = Discover(client_id=self.client_id, client_secret=self.client_secret, base_url=self.base_url)
            result_filter = ""
            host_lookup = discover.query_hosts(filter=result_filter, limit=DISCOVER_PAGE_SIZE)
            if host_lookup["status_code"] == 200:
                code = 0
            else:
                code = 1
        except Exception as e:
            context().logger.error("Test connection failed, error:%s", e)
            code = 1
        return code

    def get_hosts(self, last_model_state_id=None):
        """
        Fetch the complete host records from data source using pagination.
        parameters:
            last_model_state_id(int): Last run time(epoch time)
        returns:
            hosts(list): host list
        """
        hosts = []
        try:
            discover = Discover(client_id=self.client_id, client_secret=self.client_secret, base_url=self.base_url)
            result_filter = ""
            if last_model_state_id:
                result_filter = f"last_seen_timestamp:>'{epoch_to_datetime_conv(last_model_state_id)}'"
            host_lookup = discover.query_hosts(filter=result_filter, limit=DISCOVER_PAGE_SIZE)
            is_paged_result = True
            while is_paged_result:
                if host_lookup["status_code"] == 200:
                    identified_hosts = host_lookup["body"]["resources"]
                    host_detail = discover.get_hosts(ids=identified_hosts)
                    hosts.extend(host_detail["body"]["resources"])
                else:
                    error_detail = host_lookup["body"]["errors"]
                    for err in error_detail:
                        raise DatasourceFailure(err["message"], err["code"])
                if len(hosts) < host_lookup['body']['meta']['pagination']['total']:
                    offset = len(hosts)
                    host_lookup = discover.query_hosts(filter=result_filter, limit=DISCOVER_PAGE_SIZE, offset=offset)
                else:
                    is_paged_result = False
        except Exception as ex:
            raise DatasourceFailure(ex)
        return hosts

    def get_applications(self, app_filter=None, last_model_state_id=None):
        """
        Fetch the complete application records from data source using pagination.
        parameters:
            last_model_state_id(int): Last run time(epoch time)
        returns:
            applications(list): application list
        """
        applications = []
        try:
            discover = Discover(client_id=self.client_id, client_secret=self.client_secret, base_url=self.base_url)
            result_filter = ""
            if app_filter:
                result_filter = app_filter
            if last_model_state_id:
                installed_app_filter = f"last_updated_timestamp:>'{epoch_to_datetime_conv(last_model_state_id)}'"
                used_app_filter = f"last_used_timestamp:>'{epoch_to_datetime_conv(last_model_state_id)}'"
                result_filter = f"{installed_app_filter},{used_app_filter}"
            app_lookup = discover.query_applications(filter=result_filter, limit=DISCOVER_PAGE_SIZE)
            is_paged_result = True
            while is_paged_result:
                if app_lookup["status_code"] == 200:
                    identified_apps = app_lookup["body"]["resources"]
                    apps_detail = discover.get_applications(ids=identified_apps)
                    applications.extend(apps_detail["body"]["resources"])
                else:
                    error_detail = app_lookup["body"]["errors"]
                    for err in error_detail:
                        raise DatasourceFailure(err["message"], err["code"])
                if len(applications) < app_lookup['body']['meta']['pagination']['total']:
                    offset = len(applications)
                    app_lookup = discover.query_applications(filter=result_filter, limit=DISCOVER_PAGE_SIZE,
                                                             offset=offset)
                else:
                    is_paged_result = False
        except Exception as ex:
            raise DatasourceFailure(ex)
        return applications

    def get_accounts(self, last_model_state_id=None):
        """
        Fetch the account records from data source using pagination.
        parameters:
            last_model_state_id(int): Last run time(epoch time)
        returns:
            accounts(list): account list
        """
        accounts = []
        try:
            discover = Discover(client_id=self.client_id, client_secret=self.client_secret, base_url=self.base_url)
            result_filter = ""
            if last_model_state_id:
                result_filter = f"first_seen_timestamp:>'{epoch_to_datetime_conv(last_model_state_id)}'," \
                                f"last_successful_login_timestamp:>'{epoch_to_datetime_conv(last_model_state_id)}'"

            account_lookup = discover.query_accounts(filter=result_filter, limit=DISCOVER_PAGE_SIZE)
            is_paged_result = True
            while is_paged_result:
                if account_lookup["status_code"] == 200:
                    identified_accounts = account_lookup["body"]["resources"]
                    accounts_detail = discover.get_accounts(ids=identified_accounts)
                    accounts.extend(accounts_detail["body"]["resources"])
                else:
                    error_detail = account_lookup["body"]["errors"]
                    for err in error_detail:
                        raise DatasourceFailure(err["message"], err["code"])
                if len(accounts) < account_lookup['body']['meta']['pagination']['total']:
                    offset = len(accounts)
                    account_lookup = discover.query_accounts(filter=result_filter, limit=DISCOVER_PAGE_SIZE,
                                                             offset=offset)
                else:
                    is_paged_result = False
        except Exception as ex:
            raise DatasourceFailure(ex)
        return accounts

    def get_logins(self, user_accounts):
        """
        Fetch the user login records from data source using pagination.
        parameters:
            user_accounts(list): user accounts from manged hosts
        returns:
            account_login(list): account login event list
        """
        user_logins = []
        try:
            discover = Discover(client_id=self.client_id, client_secret=self.client_secret, base_url=self.base_url)
            account_ids = [account['id'] for account in user_accounts if account]
            for i in range(0, len(account_ids), 100):
                res_filter = "', account_id:'".join(account_ids[i:i+100])
                login_lookup = discover.query_logins(filter=f"account_id:'{res_filter}'", sort='login_timestamp.desc',
                                                     limit=DISCOVER_PAGE_SIZE)
                is_paged_result = True
                login_events = []
                user_ids = []
                while is_paged_result:
                    if login_lookup["status_code"] == 200:
                        identified_logins = login_lookup["body"]["resources"]
                        logins_detail = discover.get_logins(ids=identified_logins)
                        for event in logins_detail["body"]["resources"]:
                            if event['account_id'] not in user_ids:
                                user_ids.append(event['account_id'])
                                user_logins.append(event)
                        login_events.extend(logins_detail["body"]["resources"])
                    else:
                        error_detail = login_lookup["body"]["errors"]
                        for err in error_detail:
                            DatasourceFailure(err["message"], err["code"])
                    if len(login_events) < login_lookup['body']['meta']['pagination']['total']:
                        offset = len(login_events)
                        login_lookup = discover.query_logins(filter=f"account_id:'{res_filter}'",
                                                             sort='login_timestamp.desc', limit=DISCOVER_PAGE_SIZE,
                                                             offset=offset)
                    else:
                        is_paged_result = False
        except Exception as ex:
            raise DatasourceFailure(ex)
        return user_logins

    def get_vulnerabilities(self, last_model_state_id=None):
        """
        Fetch the vulnerability records from data source using pagination.
        parameters:
            last_model_state_id(int): Last run time(epoch time)
        returns:
            vulnerabilities(list): vulnerability list
        """
        vulnerabilities = []
        try:
            spotlight = SpotlightVulnerabilities(client_id=self.client_id, client_secret=self.client_secret,
                                                 base_url=self.base_url)
            facet = {"cve", "host_info", "remediation", "evaluation_logic"}
            result_filter = "status:['open', 'reopen']"
            if last_model_state_id:
                result_filter = f"updated_timestamp:>'{epoch_to_datetime_conv(last_model_state_id)}'+" \
                                f"(created_timestamp:>'{epoch_to_datetime_conv(last_model_state_id)}'," \
                                f"status:['open', 'closed', 'reopen'])"
            vuln_lookup = spotlight.query_vulnerabilities_combined(filter=result_filter, facet=facet,
                                                                   limit=SPOTLIGHT_PAGE_SIZE)
            after = 'true'
            while after:
                if vuln_lookup["status_code"] == 200:
                    vuln_list = vuln_lookup["body"]["resources"]
                    vulnerabilities.extend(vuln_list)
                else:
                    error_detail = vuln_lookup["body"]["errors"]
                    for err in error_detail:
                        raise DatasourceFailure(err["message"], err["code"])
                if 'after' in vuln_lookup['body']['meta']['pagination']:
                    after = vuln_lookup['body']['meta']['pagination']['after']
                vuln_lookup = spotlight.query_vulnerabilities_combined(filter=result_filter, facet=facet,
                                                                       limit=SPOTLIGHT_PAGE_SIZE, after=after)
        except Exception as ex:
            raise DatasourceFailure(ex)
        return vulnerabilities

    def get_vulnerable_applications(self, vulnerabilities, agent_application_map):
        """add application id details to the vulnerability apps sections"""
        for vuln in vulnerabilities:
            agent_id = vuln['aid']
            for vuln_app in vuln['apps']:
                product_name = vuln_app['product_name_version']
                product_version = ''
                if ' ' in vuln_app['product_name_version']:
                    split_index = vuln_app['product_name_version'].rindex(' ')
                    product_name = vuln_app['product_name_version'][:split_index]
                    # Skip for Windows OS related vulnerabilities
                    if product_name in ['Windows Server']:
                        continue
                    product_version = vuln_app['product_name_version'][split_index+1:]
                    if not re.match('[1-9]', product_version):
                        product_name = vuln_app['product_name_version']
                        product_version = ''
                if deep_get(agent_application_map, [agent_id]):
                    for agent_app in agent_application_map[agent_id]:
                        if product_version and deep_get(agent_app, ['name']) \
                                and product_name in deep_get(agent_app, ['name']) \
                                and deep_get(agent_app, ['version']) \
                                and product_version in deep_get(agent_app, ['version']):
                            app_id = agent_app['id']
                            vuln_app['app_id'] = app_id
                            break
                        elif product_name and deep_get(agent_app, ['name']) \
                                and product_name in deep_get(agent_app, ['name']):
                            app_id = agent_app['id']
                            vuln_app['app_id'] = app_id
                            break
                else:
                    app_filter = f"host.aid:'{agent_id}'+name:*'*{product_name}*'+version:*'{product_version}*'"
                    app_details = self.get_applications(app_filter)
                    for app in app_details:
                        app_id = app['id']
                        vuln_app['app_id'] = app_id
