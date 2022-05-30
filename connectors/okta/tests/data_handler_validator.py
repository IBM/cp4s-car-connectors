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

