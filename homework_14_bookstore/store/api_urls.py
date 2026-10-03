from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from .api_views import (
    BookViewSet,
    CartViewSet,
    CategoryViewSet,
    OrderViewSet,
)


router = DefaultRouter()
router.register('books', BookViewSet, basename='book')
router.register('categories', CategoryViewSet, basename='category')
router.register('orders', OrderViewSet, basename='order')
router.register('cart', CartViewSet, basename='cart')


urlpatterns = [
    path(
        'token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh',
    ),
    path(
        'token/verify/',
        TokenVerifyView.as_view(),
        name='token_verify',
    ),
    path(
        'schema/',
        SpectacularAPIView.as_view(
            permission_classes=[AllowAny]
        ),
        name='schema',
    ),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(
            url_name='schema',
            permission_classes=[AllowAny],
        ),
        name='api_docs',
    ),
    path('', include(router.urls)),
]
