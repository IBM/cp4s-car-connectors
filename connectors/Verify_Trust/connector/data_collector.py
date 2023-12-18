import json
from datetime import datetime, timedelta

from car_framework.context import context

# This is to disable context().fooMember error in IDE
# pylint: disable=no-member

QUERY_FORMAT = r"('{}')"

def deep_get(_dict, keys, default=None):
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict


def get_n_days_ago(days_ago=15):
    date_n_days_ago = datetime.now() - timedelta(days=days_ago)
    return date_n_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def timestamp_conv(time_string):
    time_pattern = "%Y-%m-%dT%H:%M:%S"
    epoch = datetime(1970, 1, 1)
    converted_time = int(((datetime.strptime(str(time_string)[:19], time_pattern) - epoch).total_seconds()) * 1000)
    return converted_time


def epoch_to_datetime_conv(epoch_time):
        epoch_time = float(epoch_time) / 1000.0
        datetime_time = datetime.fromtimestamp(epoch_time)
        return datetime_time


def datetime_format_to_ISO_8601(dt):
        time_pattern = "%Y-%m-%dT%H:%M:%SZ"
        return dt.strftime(time_pattern)


def parse_machine_ids(map_all_machine, flag=True):
    """Combining machine ids for query"""
    temp, list_id, n = [], [], 150
    for record in map_all_machine:
        if flag:
            if record['healthStatus'] in \
                    ['Active', 'ImpairedCommunication', 'NoSensorData', 'NoSensorDataImpairedCommunication']:
                temp.append(record['id'])
        elif not flag:
            temp.append(record['id'])
    final = [temp[i * n:(i + 1) * n] for i in range((len(temp) + n - 1) // n)]
    for ids in final:
        if len(ids) != 1:
            list_id.append(tuple(ids))
        elif len(ids) == 1:
            list_id.append(QUERY_FORMAT.format(ids[0]))
    return list_id


def convert_mac_format(string):
    groups = [string[i:i + 2] for i in range(0, len(string), 2)]
    return ':'.join(groups)


def create_logic_check(compare_time):
    if len(compare_time) == 28:
        first_seen_time = datetime.strptime(compare_time[:-2] + 'Z', "%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        first_seen_time = datetime.strptime(compare_time, "%Y-%m-%dT%H:%M:%S.%fZ")

    last_runtime = datetime.strptime(datetime_format_to_ISO_8601(epoch_to_datetime_conv(context().last_model_state_id)), "%Y-%m-%dT%H:%M:%SZ")
    # create flag
    if first_seen_time >= last_runtime:
        return True
    else:
        # update flag
        return False


class DataCollector(object):

    _collected_data = {}
    user_list, update_edge = list(), list()

    def _get_collected_data(self, data):
        if not self._collected_data.get(data):
            self._collected_data[data] = context().asset_server.get_request_data()
        return self._collected_data[data]

            
    
    def create_asset_host(self, incremental=True):
        """asset node creation for initial and incremental report"""
        asset_list = []
        
        # initial import case
        if not incremental:
            data = self._get_collected_data('all_machine')
            asset_list.extend(data["value"])

        elif incremental:
            data = self._get_collected_data('incremental_machine')
            for record in data["value"]:
                # create
                create_logic = create_logic_check(record['firstSeen'])
                if create_logic:
                    asset_list.append(record)
        return asset_list


    def create_ipaddress(self, incremental=True):
        """ip_address mac_address node creation for initial and incremental report"""
        if not incremental:
            data = self._get_collected_data('single_res_data')
        return data
    
    def create_browser(self, incremental=True):
        """ip_address mac_address node creation for initial and incremental report"""
        if not incremental:
            data = self._get_collected_data('single_res_data')
        return data

    def create_risk(self, incremental=True):
        if not incremental:
            data = self._get_collected_data('single_res_data')
        return data

    def create_user(self, incremental=True):
        if not incremental:
            data = self._get_collected_data('single_res_data')
        return data
