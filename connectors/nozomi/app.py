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
                                 type=str, required=False, help='Nozomi API Base URL')
        self.parser.add_argument('-port', dest='CONNECTION_PORT',
                                 default=os.getenv('CONNECTION_PORT', None),
                                 type=int, required=False, help='Nozomi API Listening Port')
        self.parser.add_argument('-key_name', dest='CONFIGURATION_AUTH_KEY_NAME',
                                 default=os.getenv('CONFIGURATION_AUTH_KEY_NAME', None),
                                 type=str, required=False, help='API Key Name')
        self.parser.add_argument('-key_token', dest='CONFIGURATION_AUTH_KEY_TOKEN',
                                 default=os.getenv('CONFIGURATION_AUTH_KEY_TOKEN', None),
                                 type=str, required=False, help='API key Token')
        self.parser.add_argument('-data_retention_period', dest='CONNECTION_OPTIONS_DATA_RETENTION_PERIOD',
                                 default=os.getenv('CONNECTION_OPTIONS_DATA_RETENTION_PERIOD', None),
                                 type=int, required=False, help='Data Retention Period')

    def setup(self):
        super().setup()
        # Set default values if not specified
        if not context().args.CONNECTION_PORT:
            context().args.CONNECTION_PORT = 443
        if not context().args.CONNECTION_OPTIONS_DATA_RETENTION_PERIOD:
            context().args.CONNECTION_OPTIONS_DATA_RETENTION_PERIOD = 90
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()

    def get_schema_extension(self):
        return SchemaExtension(
            key='e5fdcb16-63df-417a-bc38-7379ad3f473a',
            owner='nozomi',
            version='1',
            schema='''
            {
                "vertices": [
                    {
                        "name": "asset",
                        "properties": {
                            "last_activity_time": {
                                "description": "Asset last activity timestamp, epoch in milliseconds",
                                "type": "numeric"
                            },
                            "category": {
                                "description": "Asset category, asset belongs to IT or OT or IOT",
                                "type": "text"
                            },
                            "vendor": {
                                "description": "Asset vendor name",
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
