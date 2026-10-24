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
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'rest_framework',
    'store.apps.StoreConfig',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'store.middleware.RequestLoggingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'bookstore.urls'


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


WSGI_APPLICATION = 'bookstore.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}


AUTH_PASSWORD_VALIDATORS = []


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

STATICFILES_DIRS = [BASE_DIR / 'store' / 'static']


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'store.User'

LOGIN_URL = 'store:login'
LOGIN_REDIRECT_URL = 'store:book_list'
LOGOUT_REDIRECT_URL = 'store:login'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'store': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

STRIPE_CURRENCY = os.environ.get('STRIPE_CURRENCY', 'uah')

SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')


EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'
)

EMAIL_HOST = os.environ.get('EMAIL_HOST', '')

EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))

EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')

EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL', 'BookStore <noreply@example.com>'
)


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': ('rest_framework.pagination.PageNumberPagination'),
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
        'user': '1000/hour',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


SPECTACULAR_SETTINGS = {
    'TITLE': 'BookStore API',
    'DESCRIPTION': 'REST API for BookStore.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000'
    ).split(',')
    if origin.strip()
]


# Redis cache

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

REDIS_CACHE_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/1'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_CACHE_URL,
        'TIMEOUT': 300,
        'KEY_PREFIX': 'bookstore',
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
    'generate-daily-report': {
        'task': 'store.tasks.generate_daily_report',
        'schedule': crontab(hour=1, minute=0),
    },
    'cleanup-expired-sessions': {
        'task': 'store.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=3, minute=0),
    },
}


# Reports

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
