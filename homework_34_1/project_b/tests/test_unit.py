from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.db import IntegrityError

from warehouse.apps import INTEGRATION_GROUP, MANAGERS_GROUP
from warehouse.cache_utils import get_cached_stock
from warehouse.models import Shipment, StockItem, User
from warehouse.services import change_status, create_shipment
from warehouse.tasks import generate_low_stock_report, process_backorders

from .factories import ShipmentFactory, StockItemFactory, UserFactory

pytestmark = pytest.mark.django_db


def line(book_id=1, quantity=1, title='Book'):
    return {'book_id': book_id, 'title': title, 'quantity': quantity}


def test_model_str():
    stock = StockItemFactory(title='Django', quantity=3)
    shipment = ShipmentFactory(order_id=5)

    assert str(stock) == 'Django (3)'
    assert '5' in str(shipment)


def test_user_email_is_unique():
    UserFactory(email='dup@example.com')

    with pytest.raises(IntegrityError):
        UserFactory(email='dup@example.com')


def test_groups_have_expected_permissions():
    managers = Group.objects.get(name=MANAGERS_GROUP)
    service = Group.objects.get(name=INTEGRATION_GROUP)

    assert {'manage_stock', 'manage_shipments'} <= set(
        managers.permissions.values_list('codename', flat=True)
    )
    assert set(service.permissions.values_list('codename', flat=True)) == {
        'add_shipment',
        'view_shipment',
    }


def test_create_shipment_reserves_stock():
    StockItemFactory(book_id=1, quantity=5)

    shipment, created = create_shipment(10, 'a@example.com', [line(1, 2)])

    assert created
    assert shipment.status == Shipment.STATUS_PENDING
    assert shipment.items.count() == 1
    assert StockItem.objects.get(book_id=1).quantity == 3


def test_create_shipment_is_idempotent():
    StockItemFactory(book_id=1, quantity=5)

    create_shipment(10, 'a@example.com', [line(1, 2)])
    shipment, created = create_shipment(10, 'a@example.com', [line(1, 2)])

    assert not created
    assert Shipment.objects.count() == 1
    assert StockItem.objects.get(book_id=1).quantity == 3


def test_create_shipment_merges_duplicate_lines():
    StockItemFactory(book_id=1, quantity=5)

    shipment, _ = create_shipment(1, 'a@example.com', [line(1, 2), line(1, 2)])

    assert shipment.items.count() == 1
    assert shipment.items.first().quantity == 4
    assert StockItem.objects.get(book_id=1).quantity == 1


def test_create_shipment_backorder_when_not_enough_stock():
    StockItemFactory(book_id=1, quantity=1)

    shipment, _ = create_shipment(1, 'a@example.com', [line(1, 2)])

    assert shipment.status == Shipment.STATUS_BACKORDER
    assert StockItem.objects.get(book_id=1).quantity == 1


def test_create_shipment_backorder_when_book_unknown():
    shipment, _ = create_shipment(1, 'a@example.com', [line(99, 1)])

    assert shipment.status == Shipment.STATUS_BACKORDER


def test_cancel_returns_stock():
    StockItemFactory(book_id=1, quantity=5)
    shipment, _ = create_shipment(1, 'a@example.com', [line(1, 2)])

    change_status(shipment, Shipment.STATUS_CANCELLED)

    assert StockItem.objects.get(book_id=1).quantity == 5


def test_process_backorders_fulfills_when_stock_arrives():
    shipment, _ = create_shipment(1, 'a@example.com', [line(1, 3)])
    assert shipment.status == Shipment.STATUS_BACKORDER

    StockItemFactory(book_id=1, quantity=5)

    result = process_backorders()

    shipment.refresh_from_db()

    assert shipment.status == Shipment.STATUS_PENDING
    assert StockItem.objects.get(book_id=1).quantity == 2
    assert '1' in result


def test_low_stock_report(tmp_path, settings):
    settings.REPORTS_DIR = tmp_path
    StockItemFactory(book_id=1, quantity=1, title='Low book')
    StockItemFactory(book_id=2, quantity=100, title='Plenty')

    content = Path(generate_low_stock_report()).read_text(encoding='utf-8-sig')

    assert 'Low book' in content
    assert 'Plenty' not in content


def test_stock_cache_is_invalidated_on_change(django_capture_on_commit_callbacks):
    stock = StockItemFactory(book_id=7, quantity=3)

    assert get_cached_stock(7).quantity == 3
    assert cache.get('stock:7') is not None

    stock.quantity = 9

    with django_capture_on_commit_callbacks(execute=True):
        stock.save()

    assert cache.get('stock:7') is None
    assert get_cached_stock(7).quantity == 9


def test_ensure_service_user_command(monkeypatch):
    monkeypatch.setenv('SERVICE_USERNAME', 'svc')
    monkeypatch.setenv('SERVICE_PASSWORD', 'secret-pass-123')

    call_command('ensure_service_user')

    user = User.objects.get(username='svc')

    assert user.check_password('secret-pass-123')
    assert user.has_perm('warehouse.add_shipment')
    assert not user.has_perm('warehouse.manage_stock')


def test_ensure_service_user_requires_env(monkeypatch):
    from django.core.management.base import CommandError

    monkeypatch.delenv('SERVICE_USERNAME', raising=False)
    monkeypatch.delenv('SERVICE_PASSWORD', raising=False)

    with pytest.raises(CommandError):
        call_command('ensure_service_user')