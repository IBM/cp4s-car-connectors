import math
import os
import time

from car_framework.app import BaseApp
from car_framework.context import context
from car_framework.extension import SchemaExtension
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from connector.server_access import AssetServer

version = '1.0.0'


class App(BaseApp):

    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Parameters need to connect data source
        self.parser.add_argument('-client_email', dest='CONFIGURATION_AUTH_CLIENT_EMAIL',
                                 default=os.getenv('CONFIGURATION_AUTH_CLIENT_EMAIL', None),
                                 type=str, required=False, help='GCP service account mail address')
        self.parser.add_argument('-private_key', dest='CONFIGURATION_AUTH_PRIVATE_KEY',
                                 default=os.getenv('CONFIGURATION_AUTH_PRIVATE_KEY', None),
                                 type=str, required=False, help='GCP service account private key')

    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()

    def get_schema_extension(self):
        return SchemaExtension(
            key='49d4202a-cddd-4fe2-86f9-2ee2c10b7224',
            owner='gcp',
            version='1',
            schema='''
            {
                "vertices": [
                    {
                        "name": "asset",
                        "properties": {
                            "deployment_mode": {
                                "description": "Cluster deployment type",
                                "type": "text"
                            },
                            "cluster_name": {
                                "description": "Cluster name",
                                "type": "text"
                            },
                            "node_name": {
                                "description": "Cluster node name",
                                "type": "text"
                            }
                        }
                    }
                ]
            }
            '''
        )


app = App()
app.setup()
start = math.ceil(time.time())
app.run()
end = math.ceil(time.time())
context().logger.info('Import total runtime (sec): ' + str(end - start))
