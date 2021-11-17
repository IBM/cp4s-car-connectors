import os, json


class AssetServer():
    
    def __init__(self):
        pass

    def get_administrative_logs(self, timestamp):
        return self.parse_json('activity_log_administrative.json')


    def get_security_center_alerts(self, timestamp=None):
        return self.parse_json('activity_log_security_alerts.json')


    def get_virtual_machine_details(self, resource_id=None, incremental=True):
        if resource_id is not None:
            return self.parse_json('vm_details.json')
        else:
            return self.parse_json('vm_details_testdata.json')


    def get_virtual_machine_details_by_name(self, vm_name, r_group):
        return self.parse_json('vm_details.json') 
        # return self.parse_json('vm_details_testdata.json')


    def get_network_profile(self, network_url=None, incremental=True):
        return self.parse_json('activity_log_network_details.json')


    def get_public_ipaddress(self, network_public_ipaddr_url):
        return self.parse_json('activity_log_public_ip_address.json')


    def get_security_logs(self, timestamp):
        return self.parse_json('activity_log_security.json')


    def get_application_details(self, application_url=None, incremental=True):
        return self.parse_json('activity_log_application_details.json')


    def get_application_details_by_name(self, application_name, r_group):
        return self.parse_json('activity_log_application_details.json')


    def get_sql_database_details(self, database_url=None):
        data_json = {
            "server_map" : self.get_sql_server_by_name(None, None)
        }
        return data_json

    def get_sql_database_details_by_name(self, database_name, server, r_group):
        return self.parse_json('activity_log_database_details.json')
        

    def get_all_sql_databases(self):
        json_data = {'value':[]}
        servers = self.get_sql_servers(None)

        for server in servers["value"]:
            if server['id'] == "/subscriptions/083de1fb-cd2d-4b7c-895a-2b5af1d091e8/resourceGroups/eastUS/providers/Microsoft.Sql/servers/mysqlservercar":
                databases = self.parse_json('activity_log_sql_databases.json')
                for database in databases['value']:
                    database["server_map"] = server
                json_data["value"].extend(databases["value"])
        return json_data


    def get_resource_groups(self):
        return None


    def get_sql_servers(self, r_group):
        return self.parse_json('activity_log_server_details.json')
        

    def get_sql_server_by_name(self, r_group, server):
        return self.parse_json('Sql_server_details.json')


    def parse_json(self, filename):
        cur_path = os.path.dirname(__file__)
        abs_file_path = os.path.join(cur_path, "../", "tests", "azure_test_log", filename)
        json_file = open(abs_file_path)
        json_str = json_file.read()
        json_data = json.loads(json_str)
        return json_data