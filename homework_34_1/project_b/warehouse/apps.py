from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate

MANAGERS_GROUP = 'Warehouse Managers'
INTEGRATION_GROUP = 'Integration Services'

GROUP_PERMISSIONS = {
    MANAGERS_GROUP: [
        'manage_stock',
        'manage_shipments',
        'view_stockitem',
        'view_shipment',
    ],
    INTEGRATION_GROUP: [
        'add_shipment',
        'view_shipment',
    ],
}


def create_default_groups(sender, using=DEFAULT_DB_ALIAS, **kwargs):
    from django.contrib.auth.models import Group, Permission

    for name, codenames in GROUP_PERMISSIONS.items():
        group, _ = Group.objects.using(using).get_or_create(name=name)
        permissions = Permission.objects.using(using).filter(
            content_type__app_label='warehouse',
            codename__in=codenames,
        )
        group.permissions.set(permissions)


class WarehouseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'warehouse'

    def ready(self):
        from . import signals

        post_migrate.connect(
            create_default_groups,
            sender=self,
            dispatch_uid='warehouse_create_default_groups',
        )