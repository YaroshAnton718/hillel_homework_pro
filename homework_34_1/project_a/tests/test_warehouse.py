import json
from unittest.mock import patch

import pytest
import requests
import responses
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from store.apps import MANAGERS_GROUP
from store.tasks import notify_warehouse
from store.warehouse_client import (
    TOKEN_CACHE_KEY,
    WarehouseClient,
    WarehouseNotFound,
    WarehouseRejected,
    WarehouseUnavailable,
)

from .factories import OrderFactory, OrderItemFactory, UserFactory

pytestmark = pytest.mark.django_db

BASE = 'http://warehouse.test/api'
TOKEN_URL = f'{BASE}/token/'
SHIPMENTS_URL = f'{BASE}/shipments/'


@pytest.fixture(autouse=True)
def warehouse_settings(settings):
    settings.WAREHOUSE_API_URL = BASE
    settings.WAREHOUSE_SERVICE_USERNAME = 'svc'
    settings.WAREHOUSE_SERVICE_PASSWORD = 'secret'
    settings.WAREHOUSE_TIMEOUT = 1


@pytest.fixture
def mock_http():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def order_with_item():
    order = OrderFactory()
    OrderItemFactory(order=order, quantity=2)
    return order


def add_token(mock_http, token='tok'):
    mock_http.add('POST', TOKEN_URL, json={'access': token, 'refresh': 'r'})



def test_client_creates_shipment(mock_http, order_with_item):
    add_token(mock_http)
    mock_http.add(
        'POST', SHIPMENTS_URL, json={'status': 'pending'}, status=201
    )

    result = WarehouseClient().create_shipment(order_with_item)

    assert result['status'] == 'pending'

    request = mock_http.calls[1].request
    body = json.loads(request.body)

    assert request.headers['Authorization'] == 'Bearer tok'
    assert body['order_id'] == order_with_item.pk
    assert body['items'][0]['quantity'] == 2


def test_client_reuses_cached_token(mock_http):
    add_token(mock_http)
    mock_http.add('GET', f'{SHIPMENTS_URL}1/', json={'order_id': 1})

    client = WarehouseClient()
    client.get_shipment(1)
    client.get_shipment(1)

    token_calls = [c for c in mock_http.calls if c.request.url == TOKEN_URL]

    assert len(token_calls) == 1


def test_client_refreshes_expired_token(mock_http):
    cache.set(TOKEN_CACHE_KEY, 'old', 60)
    url = f'{SHIPMENTS_URL}1/'
    mock_http.add('GET', url, status=401)
    mock_http.add('GET', url, json={'order_id': 1})
    add_token(mock_http, 'new')

    assert WarehouseClient().get_shipment(1) == {'order_id': 1}
    assert mock_http.calls[-1].request.headers['Authorization'] == 'Bearer new'


@pytest.mark.parametrize(
    'status, exc',
    [
        (500, WarehouseUnavailable),
        (503, WarehouseUnavailable),
        (404, WarehouseNotFound),
        (400, WarehouseRejected),
    ],
)
def test_client_maps_http_errors(mock_http, status, exc):
    add_token(mock_http)
    mock_http.add('GET', f'{SHIPMENTS_URL}1/', status=status)

    with pytest.raises(exc):
        WarehouseClient().get_shipment(1)


def test_client_wraps_network_errors(mock_http):
    mock_http.add('POST', TOKEN_URL, body=requests.ConnectionError('down'))

    with pytest.raises(WarehouseUnavailable):
        WarehouseClient().get_shipment(1)


def test_client_login_failure(mock_http):
    mock_http.add('POST', TOKEN_URL, status=401)

    with pytest.raises(WarehouseRejected):
        WarehouseClient().get_shipment(1)



def test_notify_warehouse_success(mock_http, order_with_item):
    add_token(mock_http)
    mock_http.add('POST', SHIPMENTS_URL, json={'status': 'pending'}, status=201)

    assert 'pending' in notify_warehouse(order_with_item.pk)


def test_notify_warehouse_retries_when_unavailable(mock_http, order_with_item):
    add_token(mock_http)
    mock_http.add('POST', SHIPMENTS_URL, status=503)

    with pytest.raises(WarehouseUnavailable):
        notify_warehouse(order_with_item.pk)


def test_notify_warehouse_does_not_retry_on_rejection(mock_http, order_with_item):
    add_token(mock_http)
    mock_http.add('POST', SHIPMENTS_URL, json={'detail': 'bad'}, status=400)

    assert 'rejected' in notify_warehouse(order_with_item.pk)


def test_paid_checkout_notifies_warehouse(
    client,
    user,
    book,
    mock_notify_warehouse,
    django_capture_on_commit_callbacks,
):
    client.force_login(user)
    order = OrderFactory(user=user, total=book.price)
    OrderItemFactory(order=order, book=book, quantity=1, price=book.price)

    fake_session = type(
        'Session',
        (),
        {
            'payment_status': 'paid',
            'metadata': type(
                'Metadata', (), {'to_dict': lambda self: {'order_id': str(order.pk)}}
            )(),
        },
    )()

    with patch(
        'store.views.stripe.checkout.Session.retrieve', return_value=fake_session
    ):
        with django_capture_on_commit_callbacks(execute=True):
            client.get(reverse('store:checkout_success'), {'session_id': 'cs_1'})

    mock_notify_warehouse.assert_called_once_with(order.pk)


def make_owner_client():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return user, client


def test_order_shipment_endpoint_returns_warehouse_data(mock_http):
    user, client = make_owner_client()
    order = OrderFactory(user=user)
    add_token(mock_http)
    mock_http.add(
        'GET',
        f'{SHIPMENTS_URL}{order.pk}/',
        json={'order_id': order.pk, 'status': 'packed'},
    )

    response = client.get(reverse('order-shipment', args=[order.pk]))

    assert response.status_code == 200
    assert response.data['status'] == 'packed'


@pytest.mark.parametrize(
    'upstream_status, expected',
    [(404, 404), (500, 503), (403, 502)],
)
def test_order_shipment_endpoint_maps_errors(mock_http, upstream_status, expected):
    user, client = make_owner_client()
    order = OrderFactory(user=user)
    add_token(mock_http)
    mock_http.add('GET', f'{SHIPMENTS_URL}{order.pk}/', status=upstream_status)

    response = client.get(reverse('order-shipment', args=[order.pk]))

    assert response.status_code == expected


def test_order_shipment_endpoint_hides_foreign_orders():
    _, client = make_owner_client()
    order = OrderFactory()

    response = client.get(reverse('order-shipment', args=[order.pk]))

    assert response.status_code == 404



def test_book_managers_group_has_manage_books_permission():
    group = Group.objects.get(name=MANAGERS_GROUP)

    assert group.permissions.filter(codename='manage_books').exists()