from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import Book, Category, Order, OrderItem, User


class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = fields


class CategoryNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')
        read_only_fields = fields


class BookNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'author',
            'price',
            'stock',
        )
        read_only_fields = fields


class BookSerializer(serializers.ModelSerializer):
    category = CategoryNestedSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'author',
            'price',
            'description',
            'stock',
            'category',
            'category_id',
        )


class CategorySerializer(serializers.ModelSerializer):
    books = BookNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = (
            'id',
            'name',
            'slug',
            'books',
        )


class OrderItemSerializer(serializers.ModelSerializer):
    book = BookNestedSerializer(read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = (
            'id',
            'book',
            'quantity',
            'price',
            'subtotal',
        )
        read_only_fields = fields


class OrderItemCreateSerializer(serializers.Serializer):
    book_id = serializers.PrimaryKeyRelatedField(
        source='book',
        queryset=Book.objects.all(),
    )
    quantity = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'email',
            'total',
            'status',
            'stripe_session_id',
            'created_at',
            'items',
        )
        read_only_fields = (
            'id',
            'user',
            'total',
            'status',
            'stripe_session_id',
            'created_at',
            'items',
        )


class OrderCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError(
                'Order must contain at least one item.'
            )

        quantities = {}
        books = {}

        for item in items:
            book = item['book']
            quantity = item['quantity']

            books[book.pk] = book
            quantities[book.pk] = (
                quantities.get(book.pk, 0) + quantity
            )

        for book_id, quantity in quantities.items():
            book = books[book_id]

            if quantity > book.stock:
                raise serializers.ValidationError(
                    f'Not enough stock: {book.title}.'
                )

        return items

    def create(self, validated_data):
        request = self.context['request']
        items = validated_data.pop('items')

        email = (
            validated_data.get('email')
            or request.user.email
        )

        total = sum(
            (
                item['book'].price * item['quantity']
                for item in items
            ),
            Decimal('0.00')
        )

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                email=email,
                total=total,
            )

            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    book=item['book'],
                    quantity=item['quantity'],
                    price=item['book'].price,
                )
                for item in items
            ])

        return order

class CartItemSerializer(serializers.Serializer):
    book = BookNestedSerializer(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

class CartAddSerializer(serializers.Serializer):
    book_id = serializers.PrimaryKeyRelatedField(
        source='book',
        queryset=Book.objects.all(),
    )
    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
    )
