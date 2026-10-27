from .base import *

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,web-b').split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8001',
    'http://127.0.0.1:8001',
]