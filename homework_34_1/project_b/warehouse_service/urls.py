from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from .health import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include('warehouse.urls')),
    path('', RedirectView.as_view(pattern_name='api_docs', permanent=False)),
]