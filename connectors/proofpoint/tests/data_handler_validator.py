class TestConsumer():
    """
      Validate the API response
    """
    def handle_assets(self, obj):
        """
        Validate assets json
        """
        is_valid_asset = []
        for recipient in obj:
            assert '@' in recipient['external_id']
            is_asset = isinstance(recipient, dict)
            is_valid_asset.append(is_asset)
        return all(is_valid_asset)

    def handle_vulnerabilities(self, obj):
        """
        validate vulnerability json
        """
        is_valid_vul = []
        for threat in obj:
            assert 'external_id' in threat
            is_vul = isinstance(threat['external_id'], str)
            is_valid_vul.append(is_vul)
        return all(is_valid_vul)

    def handle_accounts(self, obj):
        """
        validate accounts json
        """
        is_valid_acc = []
        for acc in obj:
            assert acc['active'] is not None
            is_acc = acc['external_id']
            is_valid_acc.append(is_acc)
        return all(is_valid_acc)

    def handle_users(self, obj):
        """
        validate users asset json
        """
        is_valid_usr = []
        for usr in obj:
            assert usr['active'] is not None
            is_user = isinstance(usr['email'], str)
            is_valid_usr.append(is_user)
        return all(is_valid_usr)
