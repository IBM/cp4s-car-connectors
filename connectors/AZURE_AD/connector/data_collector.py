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
            if data == 'all_users':
                self._collected_data[data] = context().asset_server.get_all_users()
            elif data == 'all_groups':
                self._collected_data[data] = context().asset_server.get_all_groups()
            elif data == 'all_signins':
                self._collected_data[data] = context().asset_server.get_all_signins()
            elif data == 'all_audits':
                self._collected_data[data] = context().asset_server.get_all_audits()
            elif data == 'incremental_machine':
                self._collected_data[data] = context().asset_server.get_machine_list(
                    timestamp=datetime_format_to_ISO_8601(epoch_to_datetime_conv(context().last_model_state_id)),
                    curr_time=datetime_format_to_ISO_8601(epoch_to_datetime_conv(context().new_model_state_id)))
        return self._collected_data[data]


    def create_user(self, incremental=True):
        """user node creation for initial and incremental report"""
        if not incremental:  # initial import case
            data = self._get_collected_data('all_users')
            for user in data['value']:
                managers = context().asset_server.get_user_manager(user['id'])
                user['manager_id'] = managers['id']
            return data['value']

    def create_group(self, incremental=True):
        """group node creation for initial and incremental report"""
        if not incremental:  # initial import case
            data = self._get_collected_data('all_groups')
            return data['value']

    def create_account_group(self, incremental=True):
        """user group edge creation for initial and incremental report"""
        if not incremental:  # initial import case
            data = self._get_collected_data('all_users')
            user_groups = []
            for user in data['value']:
                u_groups = context().asset_server.get_user_groups(str(user['id']))
                for group in u_groups['value']:
                    curr_edge = {'group_id':group, 'user_id': user['id']}
                    user_groups.append(curr_edge)
            return user_groups
        
    def create_approle(self, incremental=True):
        if not incremental:
            data = self._get_collected_data('all_users')
            approles =[]
            for user in data['value']:
                user_approles = context().asset_server.get_user_approles(user['id'])
                for approle in user_approles['value']:
                    approle['user_id'] = user['id']
                    approle['type'] = 'user'
                    approles.append(approle)
            data = self._get_collected_data('all_groups')
            for group in data['value']:
                group_approles = context().asset_server.get_group_approles(group['id'])
                for approle in group_approles['value']:
                    approle['group_id'] = group['id']
                    approle['type'] = 'group'
                    approles.append(approle)
            return approles
    
    def create_permissions(self, incremental=True):
        if not incremental:
            permissions =[]
            data = self._get_collected_data('all_groups')
            for group in data['value']:
                try:
                    group_permissions = context().asset_server.get_group_permissions(group['id'])
                except:
                    continue
                for permission in group_permissions['value']:
                    permission['group_id'] = group['id']
                    permission['type'] = 'group'
                    permissions.append(permission)
            return permissions

    def create_signins(self, incremental=True):
        if not incremental:
            data = self._get_collected_data('all_signins')
            return data['value']
        
    def create_audits(self, incremental=True):
        audits = []
        if not incremental:
            data = self._get_collected_data('all_audits')
            for log in data['value']:
                if log.get('initiatedBy') and log['initiatedBy'].get('user') and log['initiatedBy']['user']:
                    log['initiatedBy']['user']['interaction_type'] = 'initiated'
                    log['account'] = [log['initiatedBy']['user']]
                    log['userId'] = log['initiatedBy']['user']['id']
                    if log['initiatedBy']['user'].get('ipAddress'):
                        log['ipAddress'] = log['initiatedBy']['user']['ipAddress']
                elif log.get('initiatedBy') and log['initiatedBy'].get('app') and log['initiatedBy']['app']:
                    log['initiatedBy']['app']['interaction_type'] = 'initiated'
                    log['app'] = [log['initiatedBy']['app']]
                for target in log['targetResources']:
                    target['interaction_type'] = 'target'
                    if target['type']=='User':
                        log['account'] = log['account'].append(target) if log.get('account')  else [target]
                    elif target['type'] == 'Group':
                        log['group'] = log['group'].append(target) if log.get('group') else [target]
                    elif target['type'] == 'Application':
                        log['app'] = log['app'].append(target) if log.get('app') else [target]
                audits.append(log)
        return audits
            
    
    def update_edges(self):
        context().logger.info('Disabling edges')
        for edge in self.update_edge:
            if 'last_modified' in edge:
                context().car_service.edge_patch(context().args.source, edge, {"last_modified": edge['last_modified']})
            else:
                context().car_service.edge_patch(context().args.source, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.update_edge))

    def delete_vertices(self):
        """Summary: Delete the Asset."""
        context().logger.info('Deleting vertices')
        asset_delete = []
        # delete Asset
        delete_machine = context().asset_server.get_machine_list(delete=get_n_days_ago(15))
        if delete_machine['value']:
            for asset in delete_machine['value']:
                asset_delete.append(asset['id'])
            if asset_delete:
                context().car_service.delete('asset', asset_delete)
        
        context().logger.info('Deleting vertices done: %s', {
            'asset': len(asset_delete)
        } )

        return asset_delete