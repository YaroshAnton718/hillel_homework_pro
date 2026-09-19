from decimal import Decimal
from unittest.mock import patch

import pytest

from django.contrib.auth.models import Permission
from django.urls import reverse

from store.cart import Cart
from store.forms import RegisterForm
from store.models import (
    Book,
    Category,
    Order,
    OrderItem,
)

from .factories import (
    BookFactory,
    CategoryFactory,
    OrderFactory,
    OrderItemFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_category_str():
    category = CategoryFactory(name='Python')
    assert str(category) == 'Python'


@pytest.mark.django_db
def test_book_str():
    book = BookFactory(title='Django')
    assert str(book) == 'Django'


@pytest.mark.django_db
def test_order_str():
    order = OrderFactory()
    assert str(order) == f'Замовлення #{order.pk}'


@pytest.mark.django_db
def test_order_item_subtotal():
    item = OrderItemFactory(
        quantity=3,
        price=Decimal('25.00')
    )
    assert item.subtotal == Decimal('75.00')


@pytest.mark.django_db
def test_user_email_unique():
    UserFactory(email='test@example.com')

    with pytest.raises(Exception):
        UserFactory(email='test@example.com')


def test_register_form_fields():
    form = RegisterForm()

    assert list(form.fields) == [
        'username',
        'email',
        'password1',
        'password2',
    ]


def test_register_form_invalid_without_data():
    form = RegisterForm()
    assert not form.is_valid()


@pytest.mark.django_db
def test_register_form_valid():
    form = RegisterForm(
        data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_register_form_creates_user():
    form = RegisterForm(
        data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }
    )

    user = form.save()

    assert user.pk is not None
    assert user.email == 'new@example.com'
    assert user.check_password('StrongPassword123!')


@pytest.mark.django_db
def test_cart_add(book, client):
    cart = Cart(client)

    cart.add(book, 2)

    assert len(cart) == 2
    assert cart.cart[str(book.pk)] == 2


@pytest.mark.django_db
def test_cart_remove(book, client):
    cart = Cart(client)

    cart.add(book, 2)
    cart.remove(book)

    assert len(cart) == 0


@pytest.mark.django_db
def test_cart_clear(book, client):
    cart = Cart(client)

    cart.add(book, 2)
    cart.clear()

    assert len(cart) == 0


@pytest.mark.django_db
def test_cart_total(book, client):
    book.price = Decimal('25.00')
    book.save()

    cart = Cart(client)
    cart.add(book, 3)

    assert cart.get_total_price() == Decimal('75.00')


@pytest.mark.django_db
def test_book_list_view(client, book):
    response = client.get(
        reverse('store:book_list')
    )

    assert response.status_code == 200
    assert book.title.encode() in response.content


@pytest.mark.django_db
def test_book_detail_view(client, book):
    response = client.get(
        reverse(
            'store:book_detail',
            args=[book.pk]
        )
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_book_create_requires_login(client):
    response = client.get(
        reverse('store:book_create')
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_book_create_requires_permission(client, user):
    client.force_login(user)

    response = client.get(
        reverse('store:book_create')
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_book_create_with_permission(client, user):
    permission = Permission.objects.get(
        codename='manage_books'
    )

    user.user_permissions.add(permission)
    client.force_login(user)

    response = client.get(
        reverse('store:book_create')
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_cart_add_view(client, book):
    response = client.post(
        reverse(
            'store:cart_add',
            args=[book.pk]
        ),
        {'quantity': 2}
    )

    assert response.status_code == 302

    cart = Cart(client)
    assert cart.cart[str(book.pk)] == 2


@pytest.mark.django_db
def test_cart_remove_view(client, book):
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
def test_cart_clear_view(client, book):
    cart = Cart(client)
    cart.add(book, 2)

    response = client.post(
        reverse('store:cart_clear')
    )

    assert response.status_code == 302
    assert len(Cart(client)) == 0


@pytest.mark.django_db
def test_checkout_empty_cart(client, user):
    client.force_login(user)

    response = client.get(
        reverse('store:checkout')
    )

    assert response.status_code == 302


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_async_book_list(async_client, book):
    response = await async_client.get(
        reverse('store:async_book_list')
    )

    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_async_book_detail(async_client, book):
    response = await async_client.get(
        reverse(
            'store:async_book_detail',
            args=[book.pk]
        )
    )

    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_async_book_count(async_client, book):
    response = await async_client.get(
        reverse('store:async_book_count')
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_checkout_uses_stripe_and_email(
    client,
    user,
    book
):
    client.force_login(user)

    cart = Cart(client)
    cart.add(book, 1)

    fake_session = type(
        'Session',
        (),
        {
            'id': 'cs_test_123',
            'url': 'https://stripe.test/session',
        }
    )()

    with patch(
        'store.views.send_mail'
    ) as email_mock, patch(
        'store.views.stripe.checkout.Session.create',
        return_value=fake_session
    ) as stripe_mock:

        response = client.get(
            reverse('store:checkout')
        )

    assert response.status_code == 302
    assert response.url == fake_session.url

    email_mock.assert_called_once()
    stripe_mock.assert_called_once()


@pytest.mark.django_db
def test_checkout_success_marks_order_paid(
    client,
    user,
    book
):
    client.force_login(user)

    order = OrderFactory(
        user=user,
        total=book.price
    )

    OrderItemFactory(
        order=order,
        book=book,
        quantity=1,
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
            {'session_id': 'cs_test_123'}
        )

    order.refresh_from_db()

    assert response.status_code == 200
    assert order.status == Order.STATUS_PAID