import csv
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import StockItem
from .services import fulfill_backorders

logger = logging.getLogger('warehouse')


@shared_task
def process_backorders():
    fulfilled = fulfill_backorders()

    logger.info('Backorders fulfilled: %s', fulfilled)

    return f'Backorders fulfilled: {fulfilled}'


@shared_task
def generate_low_stock_report():
    items = StockItem.objects.filter(
        quantity__lte=settings.LOW_STOCK_THRESHOLD
    ).order_by('quantity', 'book_id')

    reports_dir = settings.REPORTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f'low_stock_{timezone.localdate().isoformat()}.csv'

    with report_path.open(mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Book ID', 'Title', 'Quantity'])

        for item in items:
            writer.writerow([item.book_id, item.title, item.quantity])

    logger.info('Low stock report written to %s', report_path)

    return str(report_path)