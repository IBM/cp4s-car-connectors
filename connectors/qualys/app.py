import math
import time
import os

from car_framework.app import BaseApp
from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from car_framework.context import context

version = '1.0.0'


class App(BaseApp):

    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Parameters need to connect data source
        self.parser.add_argument('-qualys_url', dest='server', default=os.getenv('CONFIGURATION_AUTH_QUALYS_URL', None),
                                 type=str, required=False, help='The url of the Qualys data source')
        self.parser.add_argument('-qualys_gateway', dest='gateway', default=os.getenv('CONFIGURATION_AUTH_QUALYS_GATEWAY', None),
                                 type=str, required=False, help='The gateway of the Qualys data source')
        self.parser.add_argument('-username', dest='username', default=os.getenv('CONFIGURATION_AUTH_USERNAME', None),
                                 type=str, required=False, help='Username for the Qualys data source')
        self.parser.add_argument('-password', dest='password', default=os.getenv('CONFIGURATION_AUTH_PASSWORD', None),
                                 type=str, required=False, help='Password for the Qualys data source')

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
