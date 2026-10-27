import csv

from datetime import timedelta
from decimal import Decimal

from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail
from django.core.management import call_command
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import Order

import logging

from .warehouse_client import (
    WarehouseClient,
    WarehouseRejected,
    WarehouseUnavailable,
)

logger = logging.getLogger('store.tasks')


@shared_task
def send_order_email(order_id):
    order = Order.objects.get(pk=order_id)

    send_mail(
        subject=_('New order #%(id)s') % {'id': order.pk},
        message=_('Thank you for your order #%(id)s.\n\n' 'Order total: %(total)s UAH.')
        % {
            'id': order.pk,
            'total': order.total,
        },
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=False,
    )

    return f'Email sent for order #{order.pk}'


@shared_task
def generate_daily_report():
    report_date = timezone.localdate() - timedelta(days=1)

    statistics = Order.objects.filter(
        status=Order.STATUS_PAID, created_at__date=report_date
    ).aggregate(
        paid_orders=Count('id'),
        revenue=Sum('total'),
    )

    paid_orders = statistics['paid_orders']
    revenue = statistics['revenue'] or Decimal('0.00')

    reports_dir = settings.REPORTS_DIR

    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f'daily_report_{report_date.isoformat()}.csv'

    with report_path.open(mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                'Date',
                'Paid orders',
                'Revenue UAH',
            ]
        )

        writer.writerow(
            [
                report_date.isoformat(),
                paid_orders,
                revenue,
            ]
        )

    return str(report_path)


@shared_task
def cleanup_expired_sessions():
    call_command('clearsessions')

    return 'Expired sessions cleaned'

@shared_task(
    bind=True,
    autoretry_for=(WarehouseUnavailable,),
    retry_backoff=10,
    retry_backoff_max=600,
    retry_jitter=True,
    retry_kwargs={'max_retries': 6},
)
def notify_warehouse(self, order_id):
    order = Order.objects.get(pk=order_id)

    try:
        shipment = WarehouseClient().create_shipment(order)
    except WarehouseRejected:
        logger.error('Warehouse rejected order #%s', order_id, exc_info=True)
        return f'Warehouse rejected order #{order_id}'

    logger.info('Shipment for order #%s created in warehouse_service', order_id)

    return f'Shipment for order #{order_id} created: {shipment.get("status")}'
