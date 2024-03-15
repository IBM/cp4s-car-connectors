class TestConsumer:
    """
      Validate the API response
    """

    def handle_asset(self, obj):
        """
        Validate assets json
        """
        is_valid_cluster = []
        for asset in obj:
            assert asset['external_id'] is not None
            is_asset = isinstance(asset, dict)
            is_valid_cluster.append(is_asset)
        return all(is_valid_cluster)

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

    def handle_geo_location(self, obj):
        """
        validate geo_location json
        """
        is_geo_location = []
        for geo_location in obj:
            assert geo_location['external_id'] is not None
            is_true = isinstance(geo_location, dict)
            is_geo_location.append(is_true)
        return all(is_geo_location)

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