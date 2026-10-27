from django.apps import AppConfig
from django.db.models.signals import post_migrate

MANAGERS_GROUP = 'Book Managers'


def create_default_groups(sender, using='default', **kwargs):
    from django.contrib.auth.models import Group, Permission

    group, _ = Group.objects.using(using).get_or_create(name=MANAGERS_GROUP)
    permissions = Permission.objects.using(using).filter(
        content_type__app_label='store',
        codename='manage_books',
    )
    group.permissions.set(permissions)


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        from . import signals

        post_migrate.connect(
            create_default_groups,
            sender=self,
            dispatch_uid='store_create_default_groups',
        )