class TestConsumer:
    """
      Validate the API response
    """

    def handle_assets(self, obj):
        """
        Validate assets json
        """
        is_valid_asset = []
        for recipient in obj:
            assert recipient['external_id'] is not None
            is_asset = isinstance(recipient, dict)
            is_valid_asset.append(is_asset)
        return all(is_valid_asset)

    def handle_vulnerabilities(self, obj):
        """
        validate vulnerability json
        """
        is_valid_vul = []
        for threat in obj:
            assert threat['external_id'] is not None
            is_vul = isinstance(threat, dict)
            is_valid_vul.append(is_vul)
        return all(is_valid_vul)

    def handle_ipaddress(self, obj):
        """
        validate ipaddress json
        """
        is_valid_ip = []
        for ip_addr in obj:
            assert ip_addr['_key'] is not None
            is_ip = isinstance(ip_addr, dict)
            is_valid_ip.append(is_ip)
        return all(is_valid_ip)

    def handle_macaddress(self, obj):
        """
        validate macaddress json
        """
        is_valid_mac = []
        for mac_addr in obj:
            assert mac_addr['_key'] is not None
            is_mac = isinstance(mac_addr, dict)
            is_valid_mac.append(is_mac)
        return all(is_valid_mac)


    def handle_account(self, obj):
        """
        validate accounts json
        """
        is_account = []
        for account in obj:
            assert account['external_id'] is not None
            is_true = isinstance(account, dict)
            is_account.append(is_true)
        return all(is_account)

    def handle_hostname(self, obj):
        """
        validate hostname json
        """
        is_hostname = []
        for hostname in obj:
            assert hostname['_key'] is not None
            is_true = isinstance(hostname, dict)
            is_hostname.append(is_true)
        return all(is_hostname)

    def handle_application(self, obj):
        """
        validate application json
        """
        is_application = []
        for application in obj:
            assert application['external_id'] is not None
            is_true = isinstance(application, dict)
            is_application.append(is_true)
        return all(is_application)

    def handle_user(self, obj):
        """
        validate users json
        """
        is_user = []
        for user in obj:
            assert user['external_id'] is not None
            is_true = isinstance(user, dict)
            is_user.append(is_true)
        return all(is_user)
