import sys, argparse, traceback, os

from car_framework.context import context
from car_framework.app import BaseApp
from car_framework.extension import SchemaExtension

from connector.server_access import AssetServer
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport


version = '1.0.1'


class App(BaseApp):
    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        self.parser.add_argument('-host', dest='CONNECTION_HOST', default=os.getenv('CONNECTION_HOST',None), type=str, required=False, help='The url of the Asset data')

    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()
    

app = App()
app.setup()
app.run()
