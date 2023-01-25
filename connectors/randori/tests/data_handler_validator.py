class TestConsumer:
    """
      Validate the API response
    """

    def handle_assets(self, obj):
        """
        Validate assets json
        """
        is_valid_asset = []
        for recipient in obj['asset']:
            assert recipient['external_id'] is not None
            is_asset = isinstance(recipient, dict)
            is_valid_asset.append(is_asset)
        return all(is_valid_asset)

    def handle_ipaddress(self, obj):
        """
        validate ipaddress json
        """
        is_valid_ip = []
        for ip_addr in obj['ipaddress']:
            assert ip_addr['_key'] is not None
            is_ip = isinstance(ip_addr, dict)
            is_valid_ip.append(is_ip)
        return all(is_valid_ip)


    def handle_hostname(self, obj):
        """
        validate hostname json
        """
        is_hostname = []
        for hostname in obj['hostname']:
            assert hostname['_key'] is not None
            is_true = isinstance(hostname, dict)
            is_hostname.append(is_true)
        return all(is_hostname)

    def handle_application(self, obj):
        """
        validate application json
        """
        is_application = []
        for application in obj['application']:
            assert application['external_id'] is not None
            is_true = isinstance(application, dict)
            is_application.append(is_true)
        return all(is_application)

    def handle_ports(self, obj):
        """
        validate port json
        """
        is_user = []
        for user in obj['port']:
            assert user['external_id'] is not None
            is_true = isinstance(user, dict)
            is_user.append(is_true)
        return all(is_user)

