import argparse, os

from car_framework.context import context
from car_framework.app import BaseApp
from car_framework.extension import SchemaExtension

from connector.server_access import AssetServer
from connector.data_collector import DataCollector
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport


version = '1.0.1'


class App(BaseApp):
    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Add parameters need to connect data source
        self.parser.add_argument('-subscriptionID', dest='CONFIGURATION_AUTH_SUBSCRIPTION_ID', default=os.getenv('CONFIGURATION_AUTH_SUBSCRIPTION_ID',None), type=str, required=False, 
                            help='Subscription ID for the data source account')
        self.parser.add_argument('-tenantID', dest='CONFIGURATION_AUTH_TENANT', default=os.getenv('CONFIGURATION_AUTH_TENANT',None), type=str, required=False,
                            help='Tenant ID for data source account')
        self.parser.add_argument('-clientID', dest='CONFIGURATION_AUTH_CLIENTID', default=os.getenv('CONFIGURATION_AUTH_CLIENTID',None), type=str, required=False,
                            help='Client ID for data source account')
        self.parser.add_argument('-clientSecret', dest='CONFIGURATION_AUTH_CLIENTSECRET', default=os.getenv('CONFIGURATION_AUTH_CLIENTSECRET',None), type=str, required=False,
                            help='Client Secret value for data source account')
        self.parser.add_argument('-alerts', dest='alerts', type=bool, required=False, help=argparse.SUPPRESS)
        self.parser.add_argument('-vuln', dest='vuln', type=bool, required=False, help=argparse.SUPPRESS)


    def setup(self):
        super().setup()
        context().asset_server = AssetServer()
        context().data_collector = DataCollector()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()


    def get_schema_extension(self):
        return SchemaExtension(
            key='f1532f2f-32bf-4c39-9bcb-89643fcffd05',  # generate your own UUID key!
            owner='Reference Connector',
            version='1',
            schema='''
               {
                   "vertices": [
                        {
                           "name": "asset",
                           "properties": {
                               "os": {
                                   "description": "Operating system platform",
                                   "type": "text"
                               },
                               "os_version": {
                                   "description": "Operation system version",
                                   "type": "text"
                               },
                               "os_architecture": {
                                   "description": "Operating system architecture. Possible values are: 32-bit, 64-bit",
                                   "type": "text"
                               },
                               "ad_device_id": {
                                   "description": "Active Directory Device ID",
                                   "type": "text"
                               }
                           }
                       }
                   ]
               }
               '''
        )


app = App()
app.setup()
app.run()