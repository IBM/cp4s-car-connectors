from car_framework.inc_import import BaseIncrementalImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping, get_epoch_time, get_asset_id


class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        super().__init__()
        # initialize the data handler.
        self.data_handler = DataHandler()
        self.create_source_report_object()
        self.update_edge = []

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

    # Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.delta = context().asset_server.get_asset_collections(int(float(last_model_state_id)))
        self.last_model_state_id = last_model_state_id

    # Logic to import a collection between two save points; called by import_vertices
    def import_collection(self):
        """
        It will process the api response and does following operations
        Incremental create, Incremental update.
        returns:
            None
        """
        create_collections = self.incremental_create(self.delta)
        update_collections = self.incremental_update(self.delta)
        for collections in [create_collections, update_collections]:
            for resource in endpoint_mapping:
                for node in endpoint_mapping[resource]:
                    getattr(self.data_handler, 'handle_' + node.lower())(collections[resource])

    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        # can be left as it is if data handler manages the add edge logic
        self.data_handler.send_edges(self)

    def disable_edges(self):
        """
        Disable the inactive edges
        """
        context().logger.info('Disabling edges')
        # disable edges
        for edge in self.update_edge:
            context().car_service.edge_patch(context().args.source, edge, {"active": False})
        context().logger.info('Disabling edges done: %s', len(self.update_edge))

    def delete_vertices(self):
        """
        It will in active the edges removed from data source
        """
        context().logger.info('Delete vertices started')
        # get the un-assigned users of applications, log event type 'application.user_membership.remove'
        # disable the asset_application edge for un-assigned users.
        self.disable_app_unassigned_user_edges()
        # check if the user log-in from different client
        # disable the edge or delete old vertices.
        deleted_client_assets = self.disable_older_user_login_client_edges()
        # Disable edges
        self.disable_edges()
        # asset, application delete events
        deleted_users = self.inc_user_delete_vertices()
        deleted_apps = self.inc_app_delete_vertices()
        # merging client asset and application assets
        deleted_apps['asset'] += deleted_client_assets
        delete_resources = dict(deleted_users, **deleted_apps)
        for resource, values in delete_resources.items():
            self.inc_delete_vertices(resource, values)
        context().logger.info('Deleted vertices done: %s',
                              {key: len(value) for key, value in delete_resources.items()})

    def inc_user_delete_vertices(self):
        """
        List the user and account nodes deleted
        parameters:
        returns:
            delete_nodes(dict): dict of deleted vertices
        """
        delete_events = context().asset_server.get_systemlogs(self.last_model_state_id,
                                                              'user.lifecycle.delete.completed')
        # if user deleted, need to remove both user and account nodes.
        delete_nodes = {'user': [], 'account': []}
        # active user_account edges
        user_account_edges = self.get_active_car_edges('user_account')
        for event in delete_events:
            account_id = event['target'][0]['id']
            delete_nodes['account'].append(account_id)
            delete_user = [edge['user_id'] for edge in user_account_edges if account_id in edge['account_id']]
            delete_user = delete_user[0].split('/', 1)[1]
            delete_nodes['user'].append(delete_user)

        # user email address considered as external_id for the user node.
        # if email changes new user node will be created, this case older user node to be removed.
        for user in self.delta['user']:
            if (float(self.last_model_state_id) > get_epoch_time(user['created']) and
                    (float(self.last_model_state_id) < get_epoch_time(user['lastUpdated']))):
                updated_user = [edge['user_id'].split('/', 1)[1] for edge in user_account_edges
                                if user['id'] in edge['account_id']]
                updated_user.remove(user['profile']['email'])
                delete_nodes['user'] += updated_user

        return delete_nodes

    def inc_app_delete_vertices(self):
        """
        List the asset and application nodes deleted
        parameters:
        returns:
            delete_nodes(dict): dict of deleted vertices
        """
        delete_events = context().asset_server.get_systemlogs(self.last_model_state_id,
                                                              'application.lifecycle.delete')
        # if application deleted, need to remove both application and asset nodes.
        delete_nodes = {'asset': [], 'application': []}
        # active asset_application edges
        asset_application_edges = self.get_active_car_edges('asset_application')
        for event in delete_events:
            asset_id = event['target'][0]['id']
            delete_nodes['asset'].append(asset_id)
            delete_application = [edge['application_id'] for edge in asset_application_edges
                                  if asset_id in edge['application_id']]
            delete_application = delete_application[0].split('/', 1)[1]
            delete_nodes['application'].append(delete_application)
        return delete_nodes

    def inc_delete_vertices(self, node_type, values):
        """
        Delete vertices from CAR DB
        parameters:
            node_type(string): type of vertices
            values(list): list of resource ids
        returns:
        """
        if values:
            context().car_service.delete(node_type, values)
        context().logger.debug('Deleted asset vertices done: %s', {node_type: values,
                                                                   'len': len(values)})

    def get_active_car_edges(self, edge):
        """
        It will fetch the active edges from CAR Database
        returns:
            car_active_asset_edges(list) : list of edges
        """
        car_active_asset_edges = []
        source = context().args.source
        edge_from, edge_to = edge.split("_")
        from_id = edge_from + "_id"
        to_id = edge_to + "_id"
        edge_fields = [from_id, to_id, 'source']
        result = context().car_service.search_collection(edge, "source", source, edge_fields)
        if result:
            car_active_asset_edges = result[edge]
        return car_active_asset_edges

    def incremental_create(self, data):
        """
        It will fetch the incremental creation list
        returns:
            create_list(dict) : incremental asset, application and vulnerability list
        """
        create_list = {}
        # asset, application creation list
        for node in ['user', 'application']:
            node_list = []
            for asset in data[node]:
                if float(self.last_model_state_id) < get_epoch_time(asset['created']):
                    node_list.append(asset)
            create_list[node] = node_list
        create_list["client"] = data['client']
        return create_list

    def incremental_update(self, data):
        """
        It will fetch the incremental update list
        returns:
            update_list(dict) : incremental updated asset and vulnerability list
        """
        update_list = {}
        asset_list = []
        for user in data['user']:
            if (float(self.last_model_state_id) > get_epoch_time(user['created']) and
                    (float(self.last_model_state_id) < get_epoch_time(user['lastUpdated']) or
                     float(self.last_model_state_id) < get_epoch_time(user['lastLogin']))):
                asset_list.append(user)
        update_list["user"] = asset_list

        # application update list
        app_list = []
        for app in data['application']:
            if get_epoch_time(app['created']) < float(self.last_model_state_id) < get_epoch_time(app['lastUpdated']):
                app_list.append(app)

        # if we assign user to an application, it will not change the application update time.
        # to get users assigned to the application we need to process based on events.
        user_assign_log = context().asset_server.get_systemlogs(self.last_model_state_id,
                                                                'application.user_membership.add')
        update_list["application"] = app_list + user_assign_log
        # assign empty list for client events to endpoint mappings,
        # updates handled in function disable_edges
        update_list["client"] = []
        return update_list

    def disable_app_unassigned_user_edges(self):
        """
        Compute applications un-assigned users
        """
        user_remove_log = context().asset_server.get_systemlogs(self.last_model_state_id,
                                                                'application.user_membership.remove')
        for log in user_remove_log:
            disable_edge = {'edge_type': 'asset_account'}
            for record in log['target']:
                if record['type'] == 'AppInstance':
                    disable_edge['from'] = record['id']
                if record['type'] == 'User':
                    disable_edge['to'] = record['id']
            self.update_edge.append(disable_edge)

    def disable_older_user_login_client_edges(self):
        """
        Compute old user log-in clients needed to be deleted
        parameters:
        returns:
            delete_nodes(dict): dict of deleted vertices
        """
        delete_node = []
        active_asset_account_edges = self.get_active_car_edges('asset_account')
        for event in self.delta['client']:
            account_id = event['actor']['id']
            app_id = [record['id'] for record in event['target'] if record['type'] == 'AppInstance'][0]
            asset_id = get_asset_id(event)
            # get edges for user and application based on event
            asset_account_edges = [asset_account_edge for asset_account_edge in active_asset_account_edges
                                   if account_id in asset_account_edge['account_id']
                                   and 'app_' + app_id in asset_account_edge['asset_id']]
            for edge in asset_account_edges:
                if asset_id not in edge['asset_id']:
                    if [account['account_id'] for account in asset_account_edges
                        if (account_id not in account['account_id']) and
                            (edge['asset_id'] in account['asset_id'])]:
                        self.update_edge.append({'edge_type': 'asset_account',
                                                'from': edge['asset_id'].split('/', 1)[1],
                                                 'to': edge['account_id'].split('/', 1)[1]})
                    else:
                        delete_node.append(edge['asset_id'].split('/', 1)[1])
        return delete_node
