from .base import *

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,web').split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

INSTALLED_APPS = [*INSTALLED_APPS, 'debug_toolbar']

MIDDLEWARE = [
    *MIDDLEWARE,
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = [
    '127.0.0.1',
]
