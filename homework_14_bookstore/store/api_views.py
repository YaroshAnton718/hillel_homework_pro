from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .api_serializers import (
    BookSerializer,
    CartAddSerializer,
    CartItemSerializer,
    CategorySerializer,
    OrderCreateSerializer,
    OrderSerializer,
)
from .cart import Cart
from .models import Book, Category, Order
from .permissions import IsOwnerOrReadOnly


class AdminWritePermissionMixin:
    def get_permissions(self):
        if self.action in (
            'create',
            'update',
            'partial_update',
            'destroy',
        ):
            permission_classes = [
                IsAuthenticated,
                IsAdminUser,
            ]
        else:
            permission_classes = [IsAuthenticated]

        return [
            permission()
            for permission in permission_classes
        ]


class BookViewSet(AdminWritePermissionMixin, viewsets.ModelViewSet):
    queryset = (
        Book.objects
        .select_related('category')
        .order_by('id')
    )
    serializer_class = BookSerializer
    filterset_fields = (
        'category',
        'author',
        'stock',
    )


class CategoryViewSet(
    AdminWritePermissionMixin,
    viewsets.ModelViewSet
):
    queryset = (
        Category.objects
        .prefetch_related('books')
        .order_by('id')
    )
    serializer_class = CategorySerializer
    filterset_fields = (
        'name',
        'slug',
    )


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrReadOnly,
    ]
    filterset_fields = (
        'status',
        'email',
    )

    def get_queryset(self):
        queryset = (
            Order.objects
            .select_related('user')
            .prefetch_related('items__book')
            .order_by('-created_at')
        )

        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.is_staff:
            return queryset

        return queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer

        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        output_serializer = OrderSerializer(
            order,
            context=self.get_serializer_context(),
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class CartViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CartAddSerializer

        return CartItemSerializer

    def list(self, request):
        items = list(Cart(request))
        page = self.paginate_queryset(items)

        if page is not None:
            serializer = CartItemSerializer(
                page,
                many=True,
                context=self.get_serializer_context(),
            )
            return self.get_paginated_response(serializer.data)

        serializer = CartItemSerializer(
            items,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = serializer.validated_data['book']
        quantity = serializer.validated_data['quantity']

        cart = Cart(request)
        cart.add(book, quantity)

        item = next(
            item
            for item in cart
            if item['book'].pk == book.pk
        )

        output_serializer = CartItemSerializer(
            item,
            context=self.get_serializer_context(),
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, pk=None):
        book = get_object_or_404(Book, pk=pk)
        Cart(request).remove(book)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['delete'],
        url_path='clear',
    )
    def clear(self, request):
        Cart(request).clear()
        return Response(status=status.HTTP_204_NO_CONTENT)
