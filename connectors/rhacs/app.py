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
                                 type=str, required=False, help='The url of the RHACS data source')
        self.parser.add_argument('-token', dest='token', default=os.getenv('CONFIGURATION_AUTH_TOKEN', None),
                                 type=str, required=False, help='The authentication token of the RHACS data source')
        self.parser.add_argument('-selfSignedCert', dest='selfsignedcert',
                                 default=os.getenv('CONNECTION_SELFSIGNEDCERT', True),
                                 type=str, required=False, help='Self Signed Certificate for RHACS data source')
        self.parser.add_argument('-sni', dest='sni', default=os.getenv('CONNECTION_SNI', None),
                                 required=False, type=str,
                                 help='The SNI enables a separate hostname to be provided for SSL authentication')

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
