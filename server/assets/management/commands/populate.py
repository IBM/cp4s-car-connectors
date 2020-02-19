from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def handle(self, *args, **options):
        from assets.models import AssetModelSize
        AssetModelSize().save()