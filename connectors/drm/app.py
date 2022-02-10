import sys, argparse, traceback, os

sys.path.append('connector')

from car_framework.context import context
from car_framework.app import BaseApp

from server_access import DRMServer
from full_import import FullImport
from inc_import import IncrementalImport

version = '1.0.1'


class App(BaseApp):
    def __init__(self):
        super().__init__('This script is used for pushing IAM data to CP4S CAR database')
        self.parser.add_argument('-tenantUrl', dest='tenantUrl', default=os.getenv('CONFIGURATION_AUTH_TENANT_URL',None), type=str, required=False,
                                 help='The url of the Asset data server')
        self.parser.add_argument('-username', dest='username', default=os.getenv('CONFIGURATION_AUTH_USERNAME',None), type=str, required=False,
                                 help='The user name for the Asset data server')
        self.parser.add_argument('-password', dest='password', default=os.getenv('CONFIGURATION_AUTH_PASSWORD',None), type=str, required=False,
                                 help='The password for the Asset data server')
        self.parser.add_argument('-pageSize', dest="pageSize", default=os.getenv('CONFIGURATION_PARAMETER_PAGE_SIZE',None), type=str, required=False,
                                 help='How many records in one page')
        self.parser.add_argument('-forceFullImport', dest='forceFullImport', type=str, required=False,
                                 help='This flag forcefully attempts for full import')

    def setup(self):
        super().setup()
        context().drm_server = DRMServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()

app = App()
app.setup()
app.run()
