import sys, argparse, traceback
from context import Context
from example_full_import import ExampleFullImport
from incremental_import import IncrementalImport, Status
from server import AssetServer


version = '1.0.1'


def main():
    try:
        parser = argparse.ArgumentParser(description='This script is used for pushing asset data to CP4S CAR ingestion microservice')
        parser.add_argument('-server', dest='server', type=str, required=True, help='The url of the Asset data server')
        parser.add_argument('-username', dest='username', type=str, required=True, help='The user name for the Asset data server')
        parser.add_argument('-password', dest='password', type=str, required=True, help='The password for the Asset data server')
        parser.add_argument('-car-service', dest='car_service', type=str, required=True, help='The url of the CAR service')

        args = parser.parse_args()

        context = Context(args, 'ExampleAssetModel')
        AssetServer(context)

        importer = IncrementalImport(context)
        status = importer.run()
        if status in (Status.SUCCESS, Status.FAILURE):
            return

        importer = ExampleFullImport(context)
        importer.run()

    except Exception as e:
        traceback.print_exc()
        sys.exit(1)


main()