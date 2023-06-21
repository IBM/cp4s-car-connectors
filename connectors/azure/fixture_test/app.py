from car_framework.context import context
from car_framework.app import BaseApp

import os, sys
cur_path = os.path.dirname(__file__)
abs_file_path = os.path.join(cur_path, "../")
sys.path.append(abs_file_path)

from server_access_fake import AssetServer
from connector.data_collector import DataCollector
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport

class App(BaseApp):

    def __init__(self):
        super().__init__('CAR connector application used for extracting assets-risks from data sources '
                        ' and send it to the ingestion CARService')

    def setup(self):
        super().setup()
        context().args.CONFIGURATION_AUTH_TENANT = "1234567"
        context().args.switch = False

        context().asset_server = AssetServer()
        context().data_collector = DataCollector()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()


app = App()
app.setup()
app.run()

