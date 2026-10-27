import logging

from django.db import IntegrityError, transaction

from .models import Shipment, ShipmentItem, StockItem

logger = logging.getLogger('warehouse')


def _merge_items(items):
    merged = {}

    for item in items:
        entry = merged.setdefault(
            item['book_id'],
            {
                'book_id': item['book_id'],
                'title': item.get('title', ''),
                'quantity': 0,
            },
        )
        entry['quantity'] += item['quantity']

    return list(merged.values())


def reserve_stock(items):
    book_ids = [item['book_id'] for item in items]

    stocks = {
        stock.book_id: stock
        for stock in StockItem.objects.select_for_update()
        .filter(book_id__in=book_ids)
        .order_by('book_id')
    }

    for item in items:
        stock = stocks.get(item['book_id'])

        if stock is None or stock.quantity < item['quantity']:
            return False

    for item in items:
        stock = stocks[item['book_id']]
        stock.quantity -= item['quantity']
        stock.save(update_fields=['quantity', 'updated_at'])

    return True


def release_stock(items):
    quantities = {item['book_id']: item['quantity'] for item in items}

    stocks = StockItem.objects.select_for_update().filter(
        book_id__in=quantities.keys()
    )

    for stock in stocks:
        stock.quantity += quantities[stock.book_id]
        stock.save(update_fields=['quantity', 'updated_at'])


def create_shipment(order_id, email, items):
    existing = Shipment.objects.filter(order_id=order_id).first()

    if existing:
        logger.info('Shipment for order #%s already exists', order_id)
        return existing, False

    items = _merge_items(items)

    try:
        with transaction.atomic():
            reserved = reserve_stock(items)

            shipment = Shipment.objects.create(
                order_id=order_id,
                email=email,
                status=(
                    Shipment.STATUS_PENDING if reserved else Shipment.STATUS_BACKORDER
                ),
            )

            ShipmentItem.objects.bulk_create(
                [
                    ShipmentItem(
                        shipment=shipment,
                        book_id=item['book_id'],
                        title=item['title'],
                        quantity=item['quantity'],
                    )
                    for item in items
                ]
            )
    except IntegrityError:
        return Shipment.objects.get(order_id=order_id), False

    if reserved:
        logger.info('Shipment for order #%s created', order_id)
    else:
        logger.warning('Order #%s put on backorder: not enough stock', order_id)

    return shipment, True


@transaction.atomic
def change_status(shipment, new_status):
    shipment = Shipment.objects.select_for_update().get(pk=shipment.pk)
    old_status = shipment.status

    if new_status == Shipment.STATUS_CANCELLED and old_status in (
        Shipment.STATUS_PENDING,
        Shipment.STATUS_PACKED,
    ):
        release_stock(
            [
                {'book_id': item.book_id, 'quantity': item.quantity}
                for item in shipment.items.all()
            ]
        )

    shipment.status = new_status
    shipment.save(update_fields=['status', 'updated_at'])

    logger.info(
        'Shipment for order #%s: %s -> %s', shipment.order_id, old_status, new_status
    )

    return shipment


def fulfill_backorders():
    fulfilled = 0

    shipment_ids = list(
        Shipment.objects.filter(status=Shipment.STATUS_BACKORDER)
        .order_by('created_at')
        .values_list('pk', flat=True)
    )

    for pk in shipment_ids:
        with transaction.atomic():
            shipment = Shipment.objects.select_for_update().get(pk=pk)

            if shipment.status != Shipment.STATUS_BACKORDER:
                continue

            items = [
                {'book_id': item.book_id, 'quantity': item.quantity}
                for item in shipment.items.all()
            ]

            if reserve_stock(items):
                shipment.status = Shipment.STATUS_PENDING
                shipment.save(update_fields=['status', 'updated_at'])
                fulfilled += 1

    return fulfilled