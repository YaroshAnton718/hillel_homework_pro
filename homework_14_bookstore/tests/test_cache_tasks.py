from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from store.cache_utils import (
    get_books_cache_version,
    get_cached_book,
)
from store.models import Order
from store.tasks import (
    cleanup_expired_sessions,
    generate_daily_report,
    send_order_email,
)

from .factories import (
    BookFactory,
    CategoryFactory,
    OrderFactory,
)


@pytest.mark.django_db(transaction=True)
def test_low_level_book_cache():
    book = BookFactory()

    first_book = get_cached_book(book.pk)
    second_book = get_cached_book(book.pk)

    assert first_book.title == second_book.title
    assert cache.get(f'book:detail:{book.pk}') is not None


@pytest.mark.django_db(transaction=True)
def test_book_cache_invalidation():
    book = BookFactory(title='Original')

    get_cached_book(book.pk)

    book.title = 'Updated'
    book.save(update_fields=['title'])

    cached_book = get_cached_book(book.pk)

    assert cached_book.title == 'Updated'


@pytest.mark.django_db(transaction=True)
def test_category_cache_invalidation():
    category = CategoryFactory(name='Old category')
    book = BookFactory(category=category)

    get_cached_book(book.pk)

    category.name = 'New category'
    category.save(update_fields=['name'])

    cached_book = get_cached_book(book.pk)

    assert cached_book.category.name == 'New category'


@pytest.mark.django_db(transaction=True)
def test_book_cache_version_changes():
    old_version = get_books_cache_version()

    BookFactory()

    new_version = get_books_cache_version()

    assert old_version != new_version


@pytest.mark.django_db(transaction=True)
def test_view_cache_invalidation(client):
    BookFactory(title='First Book')

    first_response = client.get(
        reverse('store:book_list')
    )

    assert first_response.status_code == 200
    assert b'First Book' in first_response.content

    BookFactory(title='Second Book')

    second_response = client.get(
        reverse('store:book_list')
    )

    assert second_response.status_code == 200
    assert b'Second Book' in second_response.content


@pytest.mark.django_db(transaction=True)
def test_template_fragment_invalidation(client):
    book = BookFactory(description='Old description')

    url = reverse(
        'store:book_detail',
        args=[book.pk]
    )

    response = client.get(url)

    assert b'Old description' in response.content

    book.description = 'New description'
    book.save(update_fields=['description'])

    response = client.get(url)

    assert b'New description' in response.content


@pytest.mark.django_db
def test_send_order_email_task():
    order = OrderFactory()

    with patch('store.tasks.send_mail') as email_mock:
        result = send_order_email(order.pk)

    email_mock.assert_called_once()

    assert str(order.pk) in result


@pytest.mark.django_db
def test_generate_daily_report_task(tmp_path):
    order = OrderFactory(
        status=Order.STATUS_PAID,
        total=Decimal('250.00')
    )

    Order.objects.filter(pk=order.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )

    with override_settings(REPORTS_DIR=tmp_path):
        report_path = generate_daily_report()

    report = Path(report_path)

    assert report.exists()

    content = report.read_text(encoding='utf-8-sig')

    assert 'Paid orders' in content
    assert '250.00' in content


def test_cleanup_expired_sessions_task():
    with patch('store.tasks.call_command') as command_mock:
        result = cleanup_expired_sessions()

    command_mock.assert_called_once_with('clearsessions')

    assert result == 'Expired sessions cleaned'