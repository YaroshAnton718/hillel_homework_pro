from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True
    )


class Category(models.Model):
    name = models.CharField(
        _('name'),
        max_length=100
    )

    slug = models.SlugField(
        _('slug'),
        unique=True
    )

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name


class Book(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='books',
        verbose_name=_('category')
    )

    title = models.CharField(
        _('title'),
        max_length=255
    )

    author = models.CharField(
        _('author'),
        max_length=255
    )

    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2
    )

    description = models.TextField(
        _('description')
    )

    stock = models.PositiveIntegerField(
        _('stock'),
        default=0
    )

    class Meta:
        verbose_name = _('book')
        verbose_name_plural = _('books')

        permissions = [
            (
                'manage_books',
                _('Can manage books')
            ),
        ]

    def __str__(self):
        return self.title


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (
            STATUS_PENDING,
            _('Pending payment')
        ),
        (
            STATUS_PAID,
            _('Paid')
        ),
        (
            STATUS_CANCELLED,
            _('Cancelled')
        ),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('user')
    )

    email = models.EmailField(
        _('email address')
    )

    total = models.DecimalField(
        _('total'),
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    stripe_session_id = models.CharField(
        _('Stripe session ID'),
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):
        return _('Order #%(id)s') % {'id': self.pk}


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order')
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('book')
    )

    quantity = models.PositiveIntegerField(
        _('quantity')
    )

    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return _('%(book)s x %(quantity)s') % {
            'book': self.book.title,
            'quantity': self.quantity,
        }