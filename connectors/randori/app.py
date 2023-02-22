import math
import time
import os

from car_framework.app import BaseApp
from car_framework.context import context
from car_framework.extension import SchemaExtension

from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport


version = '1.0.0'


class App(BaseApp):

    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Parameters need to connect data source
        self.parser.add_argument('-host', dest='host', default=os.getenv('CONNECTION_HOST', 'app.randori.io'),
                                 type=str, required=False, help='The url of the randori data source')
        self.parser.add_argument('-access_token', dest='access_token', default=os.getenv('CONFIGURATION_AUTH_TOKEN', None),
                                 type=str, required=False, help='Authentication token for the Okta data source')

    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()

    def get_schema_extension(self):

        # The following extension adds "site" vertex collection, "site_asset" edge collection and adds "initial_value" field to "asset" collection

        return SchemaExtension(
            key = 'd1cfe02a-7296-46d9-8f59-72df470688c2',   # generate your own UUID key!
            owner = 'Randori Connector',
            version = '1',
            schema = '''
            {
                "vertices": [
                    {
                        "name": "asset",
                        "properties": {
                            "perspective_name": {
                                "description": "internal or external; from where the info for the asset is acquired",
                                "type": "text"
                            },
                            "randori_notes": {
                                "description": "Notes in randori entered by user",
                                "type": "text"
                            },
                            "first_seen": {
                                "description": "First seen by the scanner",
                                "type": "numeric"
                            },
                            "last_seen": {
                                "description": "Last seen by the scanner",
                                "type": "numeric"
                            }
                        }
                    },
                    {
                        "name": "hostname",
                        "properties": {
                            "path": {
                                "description": "path where service is running",
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
