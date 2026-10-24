from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .health import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include('store.api_urls')),
    path('', include('store.urls')),
]

if 'debug_toolbar' in settings.INSTALLED_APPS:
    urlpatterns.insert(
        0,
        path('__debug__/', include('debug_toolbar.urls')),
    )
