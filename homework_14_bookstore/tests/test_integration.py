from unittest.mock import patch

import pytest

from django.contrib.auth.models import Permission
from django.urls import reverse

from store.cart import Cart
from store.models import Order

from .factories import (
    BookFactory,
    CategoryFactory,
    UserFactory,
)

from asgiref.sync import sync_to_async


@pytest.mark.django_db
def test_user_registration_flow(client):
    response = client.post(
        reverse('store:register'),
        {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_user_login_flow(client):
    user = UserFactory(
        username='loginuser',
        email='login@example.com'
    )

    response = client.post(
        reverse('store:login'),
        {
            'username': user.username,
            'password': 'password123',
        }
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_user_logout_flow(client):
    user = UserFactory()
    client.force_login(user)

    response = client.post(
        reverse('store:logout')
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_browse_books_flow(client):
    book = BookFactory()

    response = client.get(
        reverse('store:book_list')
    )

    assert response.status_code == 200
    assert book.title.encode() in response.content


@pytest.mark.django_db
def test_book_detail_flow(client):
    book = BookFactory()

    response = client.get(
        reverse(
            'store:book_detail',
            args=[book.pk]
        )
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_add_book_to_cart_flow(client):
    book = BookFactory()

    response = client.post(
        reverse(
            'store:cart_add',
            args=[book.pk]
        ),
        {'quantity': 2}
    )

    assert response.status_code == 302
    assert Cart(client).cart[str(book.pk)] == 2


@pytest.mark.django_db
def test_remove_book_from_cart_flow(client):
    book = BookFactory()

    cart = Cart(client)
    cart.add(book, 2)

    response = client.post(
        reverse(
            'store:cart_remove',
            args=[book.pk]
        )
    )

    assert response.status_code == 302
    assert len(Cart(client)) == 0


@pytest.mark.django_db
def test_clear_cart_flow(client):
    book = BookFactory()

    cart = Cart(client)
    cart.add(book, 2)

    response = client.post(
        reverse('store:cart_clear')
    )

    assert response.status_code == 302
    assert len(Cart(client)) == 0


@pytest.mark.django_db
def test_checkout_requires_authentication(client):
    book = BookFactory()

    cart = Cart(client)
    cart.add(book)

    response = client.get(
        reverse('store:checkout')
    )

    assert response.status_code == 302
    assert '/login/' in response.url


@pytest.mark.django_db
def test_checkout_creates_order(client):
    user = UserFactory()
    book = BookFactory()

    client.force_login(user)

    cart = Cart(client)
    cart.add(book, 2)

    fake_session = type(
        'Session',
        (),
        {
            'id': 'cs_test_456',
            'url': 'https://stripe.test/checkout',
        }
    )()

    with patch(
        'store.views.send_mail'
    ), patch(
        'store.views.stripe.checkout.Session.create',
        return_value=fake_session
    ):

        response = client.get(
            reverse('store:checkout')
        )

    assert response.status_code == 302

    order = Order.objects.get(
        user=user
    )

    assert order.total == book.price * 2
    assert order.stripe_session_id == 'cs_test_456'
    assert order.items.count() == 1


@pytest.mark.django_db
def test_checkout_sends_email(client):
    user = UserFactory()
    book = BookFactory()

    client.force_login(user)

    cart = Cart(client)
    cart.add(book)

    fake_session = type(
        'Session',
        (),
        {
            'id': 'cs_email',
            'url': 'https://stripe.test/email',
        }
    )()

    with patch(
        'store.views.send_mail'
    ) as email_mock, patch(
        'store.views.stripe.checkout.Session.create',
        return_value=fake_session
    ):

        client.get(
            reverse('store:checkout')
        )

    email_mock.assert_called_once()


@pytest.mark.django_db
def test_checkout_calls_stripe(client):
    user = UserFactory()
    book = BookFactory()

    client.force_login(user)

    cart = Cart(client)
    cart.add(book)

    fake_session = type(
        'Session',
        (),
        {
            'id': 'cs_stripe',
            'url': 'https://stripe.test/payment',
        }
    )()

    with patch(
        'store.views.send_mail'
    ), patch(
        'store.views.stripe.checkout.Session.create',
        return_value=fake_session
    ) as stripe_mock:

        client.get(
            reverse('store:checkout')
        )

    stripe_mock.assert_called_once()


@pytest.mark.django_db
def test_paid_checkout_reduces_stock(client):
    user = UserFactory()
    book = BookFactory(stock=10)

    client.force_login(user)

    order = Order.objects.create(
        user=user,
        email=user.email,
        total=book.price * 2
    )

    order.items.create(
        book=book,
        quantity=2,
        price=book.price
    )

    fake_session = type(
        'Session',
        (),
        {
            'payment_status': 'paid',
            'metadata': type(
                'Metadata',
                (),
                {
                    'to_dict': lambda self: {
                        'order_id': str(order.pk)
                    }
                }
            )()
        }
    )()

    with patch(
        'store.views.stripe.checkout.Session.retrieve',
        return_value=fake_session
    ):

        response = client.get(
            reverse('store:checkout_success'),
            {'session_id': 'cs_paid'}
        )

    book.refresh_from_db()

    assert response.status_code == 200
    assert book.stock == 8


@pytest.mark.django_db
def test_paid_checkout_clears_cart(client):
    user = UserFactory()
    book = BookFactory(stock=10)

    client.force_login(user)

    cart = Cart(client)
    cart.add(book, 2)

    order = Order.objects.create(
        user=user,
        email=user.email,
        total=book.price * 2
    )

    order.items.create(
        book=book,
        quantity=2,
        price=book.price
    )

    fake_session = type(
        'Session',
        (),
        {
            'payment_status': 'paid',
            'metadata': type(
                'Metadata',
                (),
                {
                    'to_dict': lambda self: {
                        'order_id': str(order.pk)
                    }
                }
            )()
        }
    )()

    with patch(
        'store.views.stripe.checkout.Session.retrieve',
        return_value=fake_session
    ):

        client.get(
            reverse('store:checkout_success'),
            {'session_id': 'cs_clear'}
        )

    assert len(Cart(client)) == 0


@pytest.mark.django_db
def test_manager_can_create_book(client):
    user = UserFactory()

    permission = Permission.objects.get(
        codename='manage_books'
    )

    user.user_permissions.add(permission)
    client.force_login(user)

    category = CategoryFactory()

    response = client.post(
        reverse('store:book_create'),
        {
            'category': category.pk,
            'title': 'New Book',
            'author': 'New Author',
            'price': '100.00',
            'description': 'Description',
            'stock': 5,
        }
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_manager_can_update_book(client):
    user = UserFactory()
    book = BookFactory()

    permission = Permission.objects.get(
        codename='manage_books'
    )

    user.user_permissions.add(permission)
    client.force_login(user)

    response = client.post(
        reverse(
            'store:book_update',
            args=[book.pk]
        ),
        {
            'category': book.category.pk,
            'title': 'Updated',
            'author': book.author,
            'price': '200.00',
            'description': book.description,
            'stock': 7,
        }
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_manager_can_delete_book(client):
    user = UserFactory()
    book = BookFactory()

    permission = Permission.objects.get(
        codename='manage_books'
    )

    user.user_permissions.add(permission)
    client.force_login(user)

    response = client.post(
        reverse(
            'store:book_delete',
            args=[book.pk]
        )
    )

    assert response.status_code == 302


@pytest.mark.django_db(transaction=True)
async def test_async_book_list_flow(async_client):
    await sync_to_async(BookFactory)()

    response = await async_client.get(
        reverse('store:async_book_list')
    )

    assert response.status_code == 200

@pytest.mark.django_db(transaction=True)
async def test_async_book_detail_flow(async_client):
    book = await sync_to_async(BookFactory)()

    response = await async_client.get(
        reverse(
            'store:async_book_detail',
            args=[book.pk]
        )
    )

    assert response.status_code == 200

@pytest.mark.django_db(transaction=True)
async def test_async_book_count_flow(async_client):
    await sync_to_async(BookFactory)()
    await sync_to_async(BookFactory)()

    response = await async_client.get(
        reverse('store:async_book_count')
    )

    assert response.status_code == 200