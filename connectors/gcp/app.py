import math
import os
import time

from car_framework.app import BaseApp
from car_framework.context import context

from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from connector.server_access import AssetServer

version = '1.0.0'


class App(BaseApp):

    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Parameters need to connect data source
        self.parser.add_argument('-client_email', dest='client_email', default=os.getenv('CONFIGURATION_AUTH_CLIENT_EMAIL', None),
                                 type=str, required=False, help='GCP service account mail address')
        self.parser.add_argument('-certificate', dest='certificate', default=os.getenv('CONNECTION_SELFSIGNEDCERT', None),
                                 type=str, required=False, help='GCP service account private key')
        self.parser.add_argument('-page_size', dest='page_size',
                                 default=os.getenv('CONNECTION_OPTIONS_PAGE_SIZE', None),
                                 type=int, required=False, help='GCP asset inventory API response page size')

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
