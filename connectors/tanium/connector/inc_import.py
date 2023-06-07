from car_framework.inc_import import BaseIncrementalImport
from car_framework.context import context
from connector.data_handler import DataHandler, endpoint_mapping, epoch_to_datetime_conv

from string import Template

class IncrementalImport(BaseIncrementalImport):
    def __init__(self):
        # initialize the data handler.
        # If data source doesn't have external reference property None can be supplied as parameter.
        self.data_handler = DataHandler()
        super().__init__()
        self.create_source_report_object()

    # Pulls the save point for last import
    def get_new_model_state_id(self):
        return str(self.data_handler.timestamp)

    # Create source and report entry.
    def create_source_report_object(self):
        return self.data_handler.create_source_report_object()

# Gather information to get data from last save point and new save point
    def get_data_for_delta(self, last_model_state_id, new_model_state_id):
        self.last_model_state_id = last_model_state_id

    # Import all vertices from data source
    def import_vertices(self):
        context().logger.debug('Import vertices started')
        self.import_collection()
        self.data_handler.send_collections(self)

    # Import edges for all collection
    def import_edges(self):
        self.data_handler.send_edges(self)
        self.data_handler.printData()

    # Logic to import a collection; called by import_vertices
    def import_collection(self):
        """
        Process the api response and creates initial import collections
        """
        context().logger.debug('Incremental Import collection started')

        last_run = epoch_to_datetime_conv(self.last_model_state_id)
        last_run_iso = last_run.strftime('%Y-%m-%dT%H:%M:%SZ') 

        query = Template("""
            query {
                endpoints(
                    filter: {any: true, filters: [{path: "ipAddresses", op: UPDATED_AFTER, value: "${last_run_iso}"},
                    {path: "domainName", op: UPDATED_AFTER, value: "${last_run_iso}"}, 
                    {path: "macAddresses", op: UPDATED_AFTER, value: "${last_run_iso}"},
                    {path: "services.name", op: UPDATED_AFTER, value: "${last_run_iso}"},
                    {path: "installedApplications", op: UPDATED_AFTER, value: "${last_run_iso}"},
                    {path: "primaryUser.name", op: UPDATED_AFTER, value: "${last_run_iso}"},
                    {path: "risk", op: UPDATED_AFTER, value: "${last_run_iso}"},
                    {path: "deployedSoftwarePackages", op: UPDATED_AFTER, value: "${last_run_iso}"},
                    {path: "discover.openPorts", op: UPDATED_AFTER, value: "${last_run_iso}"},
                    {path: "os.name", op: UPDATED_AFTER, value: "${last_run_iso}"}]}
                ){
                    edges {
                        node {
                          id,
                          name,
                          manufacturer,
                          eidFirstSeen,
                          eidLastSeen,
                          services {
                            name,
                            displayName,
                            status
                          },
                          installedApplications {
                            name,
                            version
                          },
                          deployedSoftwarePackages {
                            id,
                            vendor,
                            version
                          },
                          ipAddress,
                          ipAddresses,
                          domainName,
                          macAddresses,
                          primaryUser{
                            name,
                            email,
                            department
                          },
                          os {
                            name
                          },
                          discover {
                            openPorts
                          },
                          risk {
                            totalScore
                          }
                      }
                    }
                }
            }
        """).substitute(locals())

        tanium_endpoints_response = context().asset_server.query_tanium_endpoints(query)

        for edge in tanium_endpoints_response['data']['endpoints']['edges']:
            tanium_node = edge['node']
            for endpoint in endpoint_mapping["tanium_endpoints"]:
                getattr(self.data_handler, 'handle_' + endpoint.lower())(tanium_node)

    def delete_vertices(self):
        pass
