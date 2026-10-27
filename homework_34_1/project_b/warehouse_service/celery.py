import os

from celery import Celery

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE', 'warehouse_service.settings.production'
)

app = Celery('warehouse_service')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()