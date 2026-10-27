import os

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from warehouse.apps import INTEGRATION_GROUP
from warehouse.models import User


class Command(BaseCommand):
    help = 'Create or update the integration account used by ProjectA.'

    def handle(self, *args, **options):
        username = os.environ.get('SERVICE_USERNAME')
        password = os.environ.get('SERVICE_PASSWORD')

        if not username or not password:
            raise CommandError('SERVICE_USERNAME and SERVICE_PASSWORD are required.')

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@service.local'},
        )
        user.set_password(password)
        user.is_active = True
        user.save()

        user.groups.add(Group.objects.get(name=INTEGRATION_GROUP))

        self.stdout.write(
            f'Service user "{username}" {"created" if created else "updated"}.'
        )