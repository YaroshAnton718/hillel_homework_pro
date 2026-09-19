from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),

    path('__debug__/', include('debug_toolbar.urls')),

    path('i18n/', include('django.conf.urls.i18n')),

    path('', include('store.urls')),
]