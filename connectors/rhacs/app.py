import math
import time
import os
from car_framework.app import BaseApp
from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from car_framework.context import context

from car_framework.extension import SchemaExtension

version = '1.0.0'


class App(BaseApp):

    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Parameters need to connect data source
        self.parser.add_argument('-host', dest='host', default=os.getenv('CONNECTION_HOST', None),
                                 type=str, required=False, help='The url of the RHACS data source')
        self.parser.add_argument('-token', dest='token', default=os.getenv('CONFIGURATION_AUTH_TOKEN', None),
                                 type=str, required=False, help='The authentication token of the RHACS data source')

    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()
    
    def get_schema_extension(self):

        # The following extension adds "site" vertex collection, "site_asset" edge collection and adds "initial_value" field to "asset" collection

        return SchemaExtension(
            key = 'c06ec385-0abc-4646-9c71-5c7a1ab8b1ad',   # generate your own UUID key!
            owner = 'Reference Connector',
            version = '2',
            schema = '''
            {
                "vertices": [
                    {
                        "name": "asset",
                        "properties": {
                            "cluster_id": {
                                "type": "text",
                                "description": "cluster_id of give node or pod"
                            },
                            "image": {
                                "type": "text",
                                "description": "image of give pod"
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
