import math
import time
import os

from car_framework.app import BaseApp
from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport
from car_framework.context import context

version = '1.0.1'


class App(BaseApp):

    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Parameters need to connect data source
        self.parser.add_argument('-proofpoint_url', dest='server', default=os.getenv('CONNECTION_HOST', None),
                                 type=str, required=False, help='The url of the ProofPoint data source')
        self.parser.add_argument('-principle', dest='username', default=os.getenv('CONFIGURATION_AUTH_PRINCIPLE', None),
                                 type=str, required=False, help='The principle for the ProofPoint data source')
        self.parser.add_argument('-secret', dest='password', default=os.getenv('CONFIGURATION_AUTH_SECRET', None),
                                 type=str, required=False, help='The secret for the Proofpoint data source')

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
