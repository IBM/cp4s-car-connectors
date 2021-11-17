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
        super().__init__('CAR connector application used for extracting assets-risks from data sources '
                        ' and send it to the ingestion CARService')
        # Add parameters need to connect data source
        self.parser.add_argument('-subscriptionID', dest='subscription_id', default=os.getenv('CONFIGURATION_AUTH_SUBSCRIPTION_ID',None), type=str, required=False, 
                            help='Subscription ID for the data source account')
        self.parser.add_argument('-tenantID', dest='tenantID', default=os.getenv('CONFIGURATION_AUTH_TENANT_ID',None), type=str, required=False,
                            help='Tenant ID for data source account')
        self.parser.add_argument('-clientID', dest='clientID', default=os.getenv('CONFIGURATION_AUTH_CLIENT_ID',None), type=str, required=False,
                            help='Client ID for data source account')
        self.parser.add_argument('-clientSecret', dest='clientSecret', default=os.getenv('CONFIGURATION_AUTH_CLIENT_SECRET',None), type=str, required=False,
                            help='Client Secret value for data source account')
        # if switch is false get vulnerability alerts, otherwise get vulnerability security
        self.parser.add_argument('-switch', dest='switch', action='store_true', help='Switch between 2 code flows')
        


    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().data_collector = DataCollector()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()


app = App()
app.setup()
app.run()

