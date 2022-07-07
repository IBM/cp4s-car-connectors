class TestConsumer:
    """
      Validate the API response
    """

    def handle_cluster(self, obj):
        """
        Validate assets json
        """
        is_valid_cluster = []
        for cluster in obj:
            assert cluster['external_id'] is not None
            is_asset = isinstance(cluster, dict)
            is_valid_cluster.append(is_asset)
        return all(is_valid_cluster)

    def handle_node(self, obj):
        """
        Validate assets json
        """
        is_valid_node = []
        for node in obj:
            assert node['external_id'] is not None
            is_asset = isinstance(node, dict)
            is_valid_node.append(is_asset)
        return all(is_valid_node)

    def handle_container(self, obj):
        """
        Validate asset & container json
        """
        is_valid_container = []
        for container in obj:
            assert container['external_id'] is not None
            is_asset = isinstance(container, dict)
            is_valid_container.append(is_asset)
        return all(is_valid_container)

    def handle_application(self, obj):
        """
        Validate application json
        """
        is_valid_application = []
        for application in obj:
            assert application['external_id'] is not None
            is_asset = isinstance(application, dict)
            is_valid_application.append(is_asset)
        return all(is_valid_application)

    def handle_account(self, obj):
        """
        Validate account json
        """
        is_valid_account = []
        for account in obj:
            assert account['external_id'] is not None
            is_asset = isinstance(account, dict)
            is_valid_account.append(is_asset)
        return all(is_valid_account)

    def handle_user(self, obj):
        """
        Validate user json
        """
        is_valid_user = []
        for user in obj:
            assert user['external_id'] is not None
            is_asset = isinstance(user, dict)
            is_valid_user.append(is_asset)
        return all(is_valid_user)

    def handle_vulnerability(self, obj):
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
