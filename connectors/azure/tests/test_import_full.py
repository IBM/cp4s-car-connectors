import unittest
from unittest.mock import patch

from tests.common_validate import context, context_patch, JsonResponse, TestConsumer


class TestAzureInitialImportFunctions(unittest.TestCase):

    @patch('connector.server_access.AssetServer.get_public_ipaddress')
    @patch('connector.server_access.AssetServer.get_network_profile')
    def test_create_ipaddress_macaddress(self, mock_get_network_profile, mock_get_public_ipaddress):
        """
             Summary unit test for create ipAddress macAddress.
        """
        context_patch(False)
        mock_get_network_profile.return_value = JsonResponse(200, 'activity_log_network_details.json').json()
        mock_get_public_ipaddress.return_value = JsonResponse(200, 'activity_log_public_ip_address.json').json()
        
        context().full_importer.create_ipaddress_macaddress()

        collections = context().full_importer.data_handler.collections
        edges = context().full_importer.data_handler.edges
        validate = TestConsumer()
        
        validations = all([
            validate.ip_adr_validate(collections.get('ipaddress')),
            validate.host_validate(collections.get('hostname')),
            validate.mac_validate(collections.get('macaddress')),
            validate.edges_validate(edges.get('ipaddress_macaddress')),
            validate.edges_validate(edges.get('asset_ipaddress')),
            validate.edges_validate(edges.get('asset_hostname')),
            validate.edges_validate(edges.get('asset_macaddress')),
        ])
        assert validations is True

    @patch('connector.server_access.AssetServer.get_virtual_machine_details_by_name')
    @patch('connector.server_access.AssetServer.get_security_center_alerts')
    def test_create_vulnerability(self, mock_get_security_center_alerts, mock_vm_details):
        """
           Summary unit test for create_vulnerability.
        """
        context_patch(False)
        mock_get_security_center_alerts.return_value = JsonResponse(200, 'activity_log_security_alerts.json').json()
        mock_vm_details.return_value = JsonResponse(200, 'vm_details.json').json()
        
        context().full_importer.create_vulnerability()

        collections = context().full_importer.data_handler.collections
        edges = context().full_importer.data_handler.edges
        validate = TestConsumer()
        
        validations = all([
            validate.vuln_validate(collections.get('vulnerability')),
            validate.edges_validate(edges.get('asset_vulnerability')),
        ])
        assert validations is True


    @patch('connector.server_access.AssetServer.get_virtual_machine_details')
    def test_create_asset_host(self, mock_vm_log_data):
        """
        Summary unit test for create_asset_host.
        """
        context_patch(False)
        mock_vm_log_data.return_value = JsonResponse(200, 'vm_details_testdata.json').json()

        context().full_importer.create_asset_host()

        collections = context().full_importer.data_handler.collections
        validate = TestConsumer()
        
        validations = all([
            validate.asset_validate(collections.get('asset')),
        ])
        assert validations is True


    @patch('connector.server_access.AssetServer.get_application_details')
    def test_create_application(self, mock_application_details):
        """
        Summary unit test for create_application.
        """
        context_patch(False)
        mock_application_details.return_value = JsonResponse(200, 'activity_log_application_details.json').json()
        
        context().full_importer.create_application()

        collections = context().full_importer.data_handler.collections
        edges = context().full_importer.data_handler.edges
        validate = TestConsumer()
        
        validations = all([
            validate.asset_validate(collections.get('asset')),
            validate.host_validate(collections.get('hostname')),
            validate.ip_adr_validate(collections.get('ipaddress')),
            validate.application_validate(collections.get('application')),
            validate.edges_validate(edges.get('asset_application')),
            validate.edges_validate(edges.get('asset_hostname')),
            validate.edges_validate(edges.get('asset_ipaddress')),
        ])
        assert validations is True

    @patch('connector.server_access.AssetServer.get_all_sql_databases')
    def test_create_database(self, mock_all_sql_databases):
        """
        Summary unit test for create_database.
        """
        context_patch(False)
        mock_all_sql_databases.return_value = JsonResponse(200, 'get_all_sql_databases_processed.json').json()
        
        context().full_importer.create_database()

        collections = context().full_importer.data_handler.collections
        edges = context().full_importer.data_handler.edges
        validate = TestConsumer()
        
        validations = all([
            validate.asset_validate(collections.get('asset')),
            validate.host_validate(collections.get('hostname')),
            validate.db_validate(collections.get('database')),
            validate.edges_validate(edges.get('asset_database')),
            validate.edges_validate(edges.get('asset_hostname')),
        ])

        assert validations is True