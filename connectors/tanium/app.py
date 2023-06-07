import math
import time
import os

from car_framework.app import BaseApp
from car_framework.context import context
# from car_framework.extension import SchemaExtension

from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport

version = '1.0.0'


class App(BaseApp):

    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Parameters need to connect data source
        self.parser.add_argument('-host', dest='CONNECTION_HOST', default=os.getenv('CONNECTION_HOST', None),
                                 type=str, required=False, help='The url of the tanium data source')
        self.parser.add_argument('-port', dest='CONNECTION_PORT', default=os.getenv('CONNECTION_PORT', 8443),
                                 type=str, required=False, help='The url of the tanium data source')
        self.parser.add_argument('-access_token', dest='CONFIGURATION_AUTH_TOKEN', default=os.getenv('CONFIGURATION_AUTH_TOKEN', None),
                                 type=str, required=False, help='Access token of the tanium data source')

    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()


app = App()
app.setup()
start = math.ceil(time.time())
app.run()
end = math.ceil(time.time())
context().logger.info('Import total runtime (sec): ' + str(end - start))
