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
        self.parser.add_argument('-host', dest='host', default=os.getenv('CONNECTION_HOST', None),
                                 type=str, required=False, help='The tenant of the Okta data source')
        self.parser.add_argument('-auth_token', dest='auth_token', default=os.getenv('CONFIGURATION_AUTH_TOKEN', None),
                                 type=str, required=False, help='Authentication token for the Okta data source')

    def setup(self):
        super().setup()

        if 'SSWS' not in self.args.auth_token:
            self.args.auth_token = 'SSWS '+ self.args.auth_token

        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()


app = App()
app.setup()
start = math.ceil(time.time())
app.run()
end = math.ceil(time.time())
context().logger.info('Import total runtime (sec): ' + str(end - start))
