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
        self.parser.add_argument('-host', dest='CONNECTION_HOST',
                                 default=os.getenv('CONNECTION_HOST', None),
                                 type=str, required=False, help='CrowdStrike API base URL excluding https://')
        self.parser.add_argument('-client_id', dest='CONFIGURATION_AUTH_CLIENT_ID',
                                 default=os.getenv('CONFIGURATION_AUTH_CLIENT_ID', None),
                                 type=str, required=False, help='Unique identifier of CrowdStrike API')
        self.parser.add_argument('-client_secret', dest='CONFIGURATION_AUTH_CLIENT_SECRET',
                                 default=os.getenv('CONFIGURATION_AUTH_CLIENT_SECRET', None),
                                 type=str, required=False, help='Secret code of CrowdStrike API client')

    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()

    def get_schema_extension(self):
        return SchemaExtension(
            key='2b1c03a1-ec5b-4208-8c34-e5d5f34e1243',
            owner='crowdstrike',
            version='1',
            schema='''
            {
                "vertices": [
                    {
                        "name": "asset",
                        "properties": {
                            "last_seen_timestamp": {
                                "description": "Host last seen timestamp in crowdstrike, epoch in milliseconds",
                                "type": "numeric"
                            },
                            "agent_id": {
                                "description": "Agent id installed on the host",
                                "type": "text"
                            }
                        }
                    },
                    {
                        "name": "account",
                        "properties": {
                            "last_successful_login_time": {
                                "description": "Last successful login timestamp of the account, epoch in milliseconds",
                                "type": "numeric"
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
