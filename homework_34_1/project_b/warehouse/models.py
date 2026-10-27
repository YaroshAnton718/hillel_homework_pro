from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)


class StockItem(models.Model):
    book_id = models.PositiveBigIntegerField(_('book ID'), unique=True)

    title = models.CharField(_('title'), max_length=255)

    quantity = models.PositiveIntegerField(_('quantity'), default=0)

    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        ordering = ['book_id']
        verbose_name = _('stock item')
        verbose_name_plural = _('stock items')

        permissions = [
            ('manage_stock', _('Can manage stock')),
        ]

    def __str__(self):
        return f'{self.title} ({self.quantity})'


class Shipment(models.Model):
    STATUS_BACKORDER = 'backorder'
    STATUS_PENDING = 'pending'
    STATUS_PACKED = 'packed'
    STATUS_SHIPPED = 'shipped'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_BACKORDER, _('Waiting for stock')),
        (STATUS_PENDING, _('Pending')),
        (STATUS_PACKED, _('Packed')),
        (STATUS_SHIPPED, _('Shipped')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    ALLOWED_TRANSITIONS = {
        STATUS_BACKORDER: {STATUS_CANCELLED},
        STATUS_PENDING: {STATUS_PACKED, STATUS_CANCELLED},
        STATUS_PACKED: {STATUS_SHIPPED, STATUS_CANCELLED},
        STATUS_SHIPPED: set(),
        STATUS_CANCELLED: set(),
    }

    order_id = models.PositiveBigIntegerField(_('order ID'), unique=True)

    email = models.EmailField(_('email address'))

    status = models.CharField(
        _('status'), max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('shipment')
        verbose_name_plural = _('shipments')

        permissions = [
            ('manage_shipments', _('Can manage shipments')),
        ]

    def __str__(self):
        return _('Shipment for order #%(id)s') % {'id': self.order_id}


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('shipment'),
    )

    book_id = models.PositiveBigIntegerField(_('book ID'))

    title = models.CharField(_('title'), max_length=255)

    quantity = models.PositiveIntegerField(_('quantity'))

    class Meta:
        verbose_name = _('shipment item')
        verbose_name_plural = _('shipment items')

    def __str__(self):
        return f'{self.title} x {self.quantity}'