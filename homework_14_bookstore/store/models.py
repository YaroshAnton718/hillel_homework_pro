from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='books'
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    description = models.TextField()
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        permissions = [
            ('manage_books', 'Can manage books'),
        ]

    def __str__(self):
        return self.title


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Очікує оплати'),
        (STATUS_PAID, 'Оплачено'),
        (STATUS_CANCELLED, 'Скасовано'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    email = models.EmailField()

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    stripe_session_id = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'Замовлення #{self.pk}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.book.title} x {self.quantity}'