from decimal import Decimal

import pytest

from django.urls import reverse
from rest_framework.test import APIClient

from store.models import Book, Order

from .factories import (
    BookFactory,
    CategoryFactory,
    OrderFactory,
    OrderItemFactory,
    UserFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_user():
    return UserFactory(
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def admin_api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.mark.django_db
def test_books_require_authentication(api_client):
    response = api_client.get(reverse('book-list'))

    assert response.status_code == 401


@pytest.mark.django_db
def test_authenticated_user_can_list_books(auth_api_client):
    BookFactory()

    response = auth_api_client.get(reverse('book-list'))

    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_book_detail_contains_nested_category(auth_api_client):
    book = BookFactory()

    response = auth_api_client.get(
        reverse('book-detail', args=[book.pk])
    )

    assert response.status_code == 200
    assert response.data['category']['id'] == book.category_id
    assert response.data['category']['name'] == book.category.name


@pytest.mark.django_db
def test_books_are_paginated_by_20(auth_api_client):
    BookFactory.create_batch(25)

    response = auth_api_client.get(reverse('book-list'))

    assert response.status_code == 200
    assert response.data['count'] == 25
    assert len(response.data['results']) == 20


@pytest.mark.django_db
def test_books_can_be_filtered_by_category(auth_api_client):
    category = CategoryFactory()
    expected = BookFactory(category=category)
    BookFactory()

    response = auth_api_client.get(
        reverse('book-list'),
        {'category': category.pk},
    )

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == expected.pk


@pytest.mark.django_db
def test_books_can_be_filtered_by_author(auth_api_client):
    expected = BookFactory(author='API Author')
    BookFactory(author='Other Author')

    response = auth_api_client.get(
        reverse('book-list'),
        {'author': 'API Author'},
    )

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == expected.pk


@pytest.mark.django_db
def test_regular_user_cannot_create_book(auth_api_client):
    category = CategoryFactory()

    response = auth_api_client.post(
        reverse('book-list'),
        {
            'category_id': category.pk,
            'title': 'REST Book',
            'author': 'Author',
            'price': '100.00',
            'description': 'Description',
            'stock': 5,
        },
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_create_book(admin_api_client):
    category = CategoryFactory()

    response = admin_api_client.post(
        reverse('book-list'),
        {
            'category_id': category.pk,
            'title': 'REST Book',
            'author': 'Author',
            'price': '100.00',
            'description': 'Description',
            'stock': 5,
        },
        format='json',
    )

    assert response.status_code == 201
    assert Book.objects.filter(title='REST Book').exists()


@pytest.mark.django_db
def test_admin_can_update_book(admin_api_client):
    book = BookFactory()

    response = admin_api_client.patch(
        reverse('book-detail', args=[book.pk]),
        {'title': 'Updated by API'},
        format='json',
    )

    book.refresh_from_db()

    assert response.status_code == 200
    assert book.title == 'Updated by API'


@pytest.mark.django_db
def test_admin_can_delete_book(admin_api_client):
    book = BookFactory()

    response = admin_api_client.delete(
        reverse('book-detail', args=[book.pk])
    )

    assert response.status_code == 204
    assert not Book.objects.filter(pk=book.pk).exists()


@pytest.mark.django_db
def test_categories_require_authentication(api_client):
    response = api_client.get(reverse('category-list'))

    assert response.status_code == 401


@pytest.mark.django_db
def test_authenticated_user_can_list_categories(auth_api_client):
    CategoryFactory()

    response = auth_api_client.get(reverse('category-list'))

    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_category_detail_contains_nested_books(auth_api_client):
    category = CategoryFactory()
    book = BookFactory(category=category)

    response = auth_api_client.get(
        reverse('category-detail', args=[category.pk])
    )

    assert response.status_code == 200
    assert response.data['books'][0]['id'] == book.pk


@pytest.mark.django_db
def test_regular_user_cannot_create_category(auth_api_client):
    response = auth_api_client.post(
        reverse('category-list'),
        {
            'name': 'REST',
            'slug': 'rest',
        },
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_create_category(admin_api_client):
    response = admin_api_client.post(
        reverse('category-list'),
        {
            'name': 'REST',
            'slug': 'rest',
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['name'] == 'REST'


@pytest.mark.django_db
def test_categories_can_be_filtered_by_slug(auth_api_client):
    expected = CategoryFactory(slug='api')
    CategoryFactory(slug='other')

    response = auth_api_client.get(
        reverse('category-list'),
        {'slug': 'api'},
    )

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == expected.pk


@pytest.mark.django_db
def test_order_list_contains_only_current_user_orders(
    auth_api_client,
    user,
):
    own_order = OrderFactory(user=user)
    OrderFactory()

    response = auth_api_client.get(reverse('order-list'))

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == own_order.pk


@pytest.mark.django_db
def test_admin_can_list_all_orders(admin_api_client):
    OrderFactory()
    OrderFactory()

    response = admin_api_client.get(reverse('order-list'))

    assert response.status_code == 200
    assert response.data['count'] == 2


@pytest.mark.django_db
def test_order_detail_contains_nested_items(
    auth_api_client,
    user,
):
    order = OrderFactory(user=user)
    item = OrderItemFactory(order=order)

    response = auth_api_client.get(
        reverse('order-detail', args=[order.pk])
    )

    assert response.status_code == 200
    assert response.data['items'][0]['id'] == item.pk
    assert response.data['items'][0]['book']['id'] == item.book_id


@pytest.mark.django_db
def test_user_cannot_read_another_users_order(
    auth_api_client,
):
    order = OrderFactory()

    response = auth_api_client.get(
        reverse('order-detail', args=[order.pk])
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_can_create_order_with_nested_items(
    auth_api_client,
    user,
):
    book = BookFactory(
        price=Decimal('75.00'),
        stock=10,
    )

    response = auth_api_client.post(
        reverse('order-list'),
        {
            'items': [
                {
                    'book_id': book.pk,
                    'quantity': 2,
                }
            ]
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['user']['id'] == user.pk
    assert Decimal(response.data['total']) == Decimal('150.00')
    assert response.data['items'][0]['book']['id'] == book.pk
    assert response.data['items'][0]['quantity'] == 2


@pytest.mark.django_db
def test_order_create_rejects_empty_items(auth_api_client):
    response = auth_api_client.post(
        reverse('order-list'),
        {'items': []},
        format='json',
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_order_create_rejects_quantity_above_stock(
    auth_api_client,
):
    book = BookFactory(stock=1)

    response = auth_api_client.post(
        reverse('order-list'),
        {
            'items': [
                {
                    'book_id': book.pk,
                    'quantity': 2,
                }
            ]
        },
        format='json',
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_owner_can_update_order_email(
    auth_api_client,
    user,
):
    order = OrderFactory(user=user)

    response = auth_api_client.patch(
        reverse('order-detail', args=[order.pk]),
        {'email': 'changed@example.com'},
        format='json',
    )

    order.refresh_from_db()

    assert response.status_code == 200
    assert order.email == 'changed@example.com'


@pytest.mark.django_db
def test_user_cannot_update_another_users_order(
    auth_api_client,
):
    order = OrderFactory()

    response = auth_api_client.patch(
        reverse('order-detail', args=[order.pk]),
        {'email': 'changed@example.com'},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_orders_can_be_filtered_by_status(
    auth_api_client,
    user,
):
    paid = OrderFactory(
        user=user,
        status=Order.STATUS_PAID,
    )
    OrderFactory(
        user=user,
        status=Order.STATUS_PENDING,
    )

    response = auth_api_client.get(
        reverse('order-list'),
        {'status': Order.STATUS_PAID},
    )

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == paid.pk


@pytest.mark.django_db
def test_cart_requires_authentication(api_client):
    response = api_client.get(reverse('cart-list'))

    assert response.status_code == 401


@pytest.mark.django_db
def test_authenticated_user_can_list_cart(auth_api_client):
    response = auth_api_client.get(reverse('cart-list'))

    assert response.status_code == 200
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_user_can_add_book_to_cart(auth_api_client):
    book = BookFactory()

    response = auth_api_client.post(
        reverse('cart-list'),
        {
            'book_id': book.pk,
            'quantity': 2,
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['book']['id'] == book.pk
    assert response.data['quantity'] == 2


@pytest.mark.django_db
def test_cart_list_contains_added_book(auth_api_client):
    book = BookFactory()

    auth_api_client.post(
        reverse('cart-list'),
        {
            'book_id': book.pk,
            'quantity': 2,
        },
        format='json',
    )

    response = auth_api_client.get(reverse('cart-list'))

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['book']['id'] == book.pk


@pytest.mark.django_db
def test_user_can_remove_book_from_cart(auth_api_client):
    book = BookFactory()

    auth_api_client.post(
        reverse('cart-list'),
        {
            'book_id': book.pk,
            'quantity': 2,
        },
        format='json',
    )

    response = auth_api_client.delete(
        reverse('cart-detail', args=[book.pk])
    )

    assert response.status_code == 204

    response = auth_api_client.get(reverse('cart-list'))
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_user_can_clear_cart(auth_api_client):
    book = BookFactory()

    auth_api_client.post(
        reverse('cart-list'),
        {
            'book_id': book.pk,
            'quantity': 2,
        },
        format='json',
    )

    response = auth_api_client.delete(
        reverse('cart-clear')
    )

    assert response.status_code == 204

    response = auth_api_client.get(reverse('cart-list'))
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_token_obtain_returns_access_and_refresh(api_client):
    user = UserFactory(username='jwtuser')

    response = api_client.post(
        reverse('token_obtain_pair'),
        {
            'username': user.username,
            'password': 'password123',
        },
        format='json',
    )

    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data


@pytest.mark.django_db
def test_token_refresh_returns_new_access_token(api_client):
    user = UserFactory(username='refreshuser')

    obtain_response = api_client.post(
        reverse('token_obtain_pair'),
        {
            'username': user.username,
            'password': 'password123',
        },
        format='json',
    )

    response = api_client.post(
        reverse('token_refresh'),
        {'refresh': obtain_response.data['refresh']},
        format='json',
    )

    assert response.status_code == 200
    assert 'access' in response.data


@pytest.mark.django_db
def test_token_verify_accepts_valid_access_token(api_client):
    user = UserFactory(username='verifyuser')

    obtain_response = api_client.post(
        reverse('token_obtain_pair'),
        {
            'username': user.username,
            'password': 'password123',
        },
        format='json',
    )

    response = api_client.post(
        reverse('token_verify'),
        {'token': obtain_response.data['access']},
        format='json',
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_jwt_access_token_authenticates_api_request(api_client):
    user = UserFactory(username='apiuser')
    BookFactory()

    obtain_response = api_client.post(
        reverse('token_obtain_pair'),
        {
            'username': user.username,
            'password': 'password123',
        },
        format='json',
    )

    api_client.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {obtain_response.data['access']}"
        )
    )

    response = api_client.get(reverse('book-list'))

    assert response.status_code == 200


@pytest.mark.django_db
def test_api_schema_is_available(api_client):
    response = api_client.get(reverse('schema'))

    assert response.status_code == 200


@pytest.mark.django_db
def test_api_docs_are_available(api_client):
    response = api_client.get(reverse('api_docs'))

    assert response.status_code == 200


@pytest.mark.django_db
def test_cors_header_is_returned_for_allowed_origin(
    auth_api_client,
):
    response = auth_api_client.get(
        reverse('book-list'),
        HTTP_ORIGIN='http://localhost:3000',
    )

    assert response.status_code == 200
    assert (
        response['Access-Control-Allow-Origin']
        == 'http://localhost:3000'
    )
