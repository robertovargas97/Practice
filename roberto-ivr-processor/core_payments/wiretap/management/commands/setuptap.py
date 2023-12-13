from django.core.management.base import BaseCommand, CommandError
from ...models import Tap


class Command(BaseCommand):
    help = 'Sets up the default tap so all requests and responses to the API are logged.'

    def handle(self, *args, **options):
        # setup wire tap so messages can be logged
        tap, created = Tap.objects.get_or_create(
            path_regex='/coreservices/payments/api/',
            defaults={'mask_chd': True, 'is_active': True}
        )
