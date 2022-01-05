import os

from car_framework.context import context
from car_framework.app import BaseApp

from connector.server_access import AssetServer
from connector.data_collector import DataCollector
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport


version = '1.0.1'


class App(BaseApp):
    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Add parameters need to connect data source
        self.parser.add_argument('-accountId', dest='accountId', default=os.getenv('CONFIGURATION_AUTH_ACCOUNT_ID',None), type=str, required=False,
                            help='account ID for the data source account')
        self.parser.add_argument('-clientID', dest='clientID', default=os.getenv('CONFIGURATION_AUTH_CLIENT_ID',None), type=str, required=False,
                            help='Client ID for data source account')
        self.parser.add_argument('-clientSecret', dest='clientSecret', default=os.getenv('CONFIGURATION_AUTH_CLIENT_SECRET',None), type=str, required=False,
                            help='Client Secret value for data source account')
        self.parser.add_argument('-region', dest='region', default=os.getenv('CONFIGURATION_PARAMETER_REGION',None), type=str, required=False,
                            help='region for data source account')


    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().data_collector = DataCollector()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()


app = App()
app.setup()
app.run()
