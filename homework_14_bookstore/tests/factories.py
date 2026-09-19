import factory

from store.models import (
    Book,
    Category,
    Order,
    OrderItem,
    User,
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(
        lambda n: f'user{n}'
    )

    email = factory.Sequence(
        lambda n: f'user{n}@example.com'
    )

    password = factory.PostGenerationMethodCall(
        'set_password',
        'password123'
    )


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(
        lambda n: f'Category {n}'
    )

    slug = factory.Sequence(
        lambda n: f'category-{n}'
    )


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    category = factory.SubFactory(
        CategoryFactory
    )

    title = factory.Sequence(
        lambda n: f'Book {n}'
    )

    author = factory.Sequence(
        lambda n: f'Author {n}'
    )

    price = factory.LazyFunction(
        lambda: 100
    )

    description = 'Test book description'

    stock = 10


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)

    email = factory.LazyAttribute(
        lambda obj: obj.user.email
    )

    total = 100

    status = Order.STATUS_PENDING


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)

    book = factory.SubFactory(BookFactory)

    quantity = 2

    price = 50