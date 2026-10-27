import os
from pathlib import Path

import sentry_sdk
from celery.schedules import crontab
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = Path(__file__).resolve().parent.parent.parent


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'drf_spectacular',
    'rest_framework',
    'warehouse.apps.WarehouseConfig',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'warehouse_service.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]


WSGI_APPLICATION = 'warehouse_service.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db-b'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}


AUTH_USER_MODEL = 'warehouse.User'


LANGUAGE_CODE = 'uk'

LANGUAGES = [
    ('uk', 'Українська'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'Europe/Kyiv'

USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        'warehouse': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '10000/hour',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


SPECTACULAR_SETTINGS = {
    'TITLE': 'Warehouse API',
    'DESCRIPTION': 'REST API for the BookStore warehouse service.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# Redis cache

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis-b')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/1',
        'TIMEOUT': 300,
        'KEY_PREFIX': 'warehouse',
    }
}


# Celery

CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/2'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300

CELERY_BEAT_SCHEDULE = {
    'process-backorders': {
        'task': 'warehouse.tasks.process_backorders',
        'schedule': crontab(minute='*/10'),
    },
    'generate-low-stock-report': {
        'task': 'warehouse.tasks.generate_low_stock_report',
        'schedule': crontab(hour=2, minute=0),
    },
}


# Warehouse

LOW_STOCK_THRESHOLD = int(os.environ.get('LOW_STOCK_THRESHOLD', '5'))

REPORTS_DIR = BASE_DIR / 'reports'


# Sentry

SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.0')),
        environment=os.environ.get('SENTRY_ENVIRONMENT', 'development'),
        send_default_pii=False,
    )