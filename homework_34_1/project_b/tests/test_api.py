import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.urls import reverse

from warehouse.apps import INTEGRATION_GROUP
from warehouse.models import Shipment, StockItem
from warehouse.services import create_shipment

from .conftest import make_client
from .factories import ShipmentFactory, StockItemFactory, UserFactory

pytestmark = pytest.mark.django_db


def payload(order_id=1, items=None):
    return {
        'order_id': order_id,
        'email': 'buyer@example.com',
        'items': items if items is not None else [
            {'book_id': 1, 'title': 'Book', 'quantity': 2}
        ],
    }

def test_shipments_require_authentication(api_client):
    assert api_client.get(reverse('shipment-list')).status_code == 401


def test_plain_user_cannot_create_or_list_shipments(user_client):
    assert user_client.post(
        reverse('shipment-list'), payload(), format='json'
    ).status_code == 403
    assert user_client.get(reverse('shipment-list')).status_code == 403


def test_jwt_flow(api_client):
    user = UserFactory(username='svc')
    user.groups.add(Group.objects.get(name=INTEGRATION_GROUP))

    response = api_client.post(
        reverse('token_obtain_pair'),
        {'username': 'svc', 'password': 'password123'},
        format='json',
    )

    assert response.status_code == 200

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')

    assert api_client.get(reverse('shipment-list')).status_code == 200


def test_service_creates_shipment_and_reserves_stock(service_client):
    StockItemFactory(book_id=1, quantity=5)

    response = service_client.post(
        reverse('shipment-list'), payload(), format='json'
    )

    assert response.status_code == 201
    assert response.data['status'] == 'pending'
    assert response.data['items'][0]['quantity'] == 2
    assert StockItem.objects.get(book_id=1).quantity == 3


def test_create_shipment_is_idempotent(service_client):
    StockItemFactory(book_id=1, quantity=5)
    url = reverse('shipment-list')

    first = service_client.post(url, payload(), format='json')
    second = service_client.post(url, payload(), format='json')

    assert first.status_code == 201
    assert second.status_code == 200
    assert Shipment.objects.count() == 1
    assert StockItem.objects.get(book_id=1).quantity == 3


def test_create_shipment_goes_to_backorder(service_client):
    StockItemFactory(book_id=1, quantity=1)

    response = service_client.post(
        reverse('shipment-list'), payload(), format='json'
    )

    assert response.status_code == 201
    assert response.data['status'] == 'backorder'
    assert StockItem.objects.get(book_id=1).quantity == 1


def test_create_shipment_validates_payload(service_client):
    response = service_client.post(
        reverse('shipment-list'), payload(items=[]), format='json'
    )

    assert response.status_code == 400


def test_service_can_retrieve_shipment_by_order_id(service_client):
    shipment = ShipmentFactory(order_id=42)

    response = service_client.get(reverse('shipment-detail', args=[42]))

    assert response.status_code == 200
    assert response.data['id'] == shipment.pk


def test_unknown_shipment_returns_404(service_client):
    assert service_client.get(reverse('shipment-detail', args=[999])).status_code == 404


def test_shipments_can_be_filtered_by_status(manager_client):
    ShipmentFactory(status=Shipment.STATUS_PACKED)
    ShipmentFactory(status=Shipment.STATUS_PENDING)

    response = manager_client.get(reverse('shipment-list'), {'status': 'packed'})

    assert response.data['count'] == 1


def test_manager_changes_status(manager_client):
    ShipmentFactory(order_id=1, status=Shipment.STATUS_PENDING)

    response = manager_client.patch(
        reverse('shipment-detail', args=[1]), {'status': 'packed'}, format='json'
    )

    assert response.status_code == 200
    assert response.data['status'] == 'packed'


def test_invalid_status_transition_is_rejected(manager_client):
    ShipmentFactory(order_id=1, status=Shipment.STATUS_SHIPPED)

    response = manager_client.patch(
        reverse('shipment-detail', args=[1]), {'status': 'pending'}, format='json'
    )

    assert response.status_code == 400


def test_cancel_via_api_returns_stock(manager_client):
    StockItemFactory(book_id=1, quantity=5)
    create_shipment(1, 'a@example.com', [{'book_id': 1, 'title': 'B', 'quantity': 2}])

    response = manager_client.patch(
        reverse('shipment-detail', args=[1]), {'status': 'cancelled'}, format='json'
    )

    assert response.status_code == 200
    assert StockItem.objects.get(book_id=1).quantity == 5


def test_service_cannot_change_status(service_client):
    ShipmentFactory(order_id=1)

    response = service_client.patch(
        reverse('shipment-detail', args=[1]), {'status': 'packed'}, format='json'
    )

    assert response.status_code == 403

def test_authenticated_user_can_read_stock_and_it_is_cached(user_client):
    StockItemFactory(book_id=7, quantity=3)

    response = user_client.get(reverse('stock-detail', args=[7]))

    assert response.status_code == 200
    assert response.data['quantity'] == 3
    assert cache.get('stock:7') is not None


def test_authenticated_user_can_list_stock(user_client):
    StockItemFactory()

    assert user_client.get(reverse('stock-list')).data['count'] == 1


def test_plain_user_cannot_create_stock(user_client):
    response = user_client.post(
        reverse('stock-list'),
        {'book_id': 1, 'title': 'Book', 'quantity': 5},
        format='json',
    )

    assert response.status_code == 403


def test_manager_creates_and_updates_stock(manager_client):
    created = manager_client.post(
        reverse('stock-list'),
        {'book_id': 1, 'title': 'Book', 'quantity': 5},
        format='json',
    )
    updated = manager_client.patch(
        reverse('stock-detail', args=[1]), {'quantity': 9}, format='json'
    )

    assert created.status_code == 201
    assert updated.status_code == 200
    assert StockItem.objects.get(book_id=1).quantity == 9


def test_unknown_stock_returns_404(user_client):
    assert user_client.get(reverse('stock-detail', args=[12345])).status_code == 404


def test_schema_and_docs_are_available(api_client):
    assert api_client.get(reverse('schema')).status_code == 200
    assert api_client.get(reverse('api_docs')).status_code == 200


def test_health_check(client):
    response = client.get(reverse('health_check'))

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'