import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-key'
)

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'web',
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'debug_toolbar',

    'store',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'store.middleware.RequestLoggingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
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

TIME_ZONE = 'Europe/Kyiv'

USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'store' / 'static'
]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'store.User'

LOGIN_URL = 'store:login'
LOGIN_REDIRECT_URL = 'store:book_list'
LOGOUT_REDIRECT_URL = 'store:login'


INTERNAL_IPS = [
    '127.0.0.1',
]


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

STRIPE_SECRET_KEY = os.environ.get(
    'STRIPE_SECRET_KEY',
    ''
)

STRIPE_CURRENCY = os.environ.get(
    'STRIPE_CURRENCY',
    'uah'
)

SITE_URL = os.environ.get(
    'SITE_URL',
    'http://localhost:8000'
)


EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)

EMAIL_HOST = os.environ.get(
    'EMAIL_HOST',
    ''
)

EMAIL_PORT = int(
    os.environ.get(
        'EMAIL_PORT',
        '587'
    )
)

EMAIL_USE_TLS = os.environ.get(
    'EMAIL_USE_TLS',
    'True'
).lower() == 'true'

EMAIL_HOST_USER = os.environ.get(
    'EMAIL_HOST_USER',
    ''
)

EMAIL_HOST_PASSWORD = os.environ.get(
    'EMAIL_HOST_PASSWORD',
    ''
)

DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    'BookStore <noreply@example.com>'
)