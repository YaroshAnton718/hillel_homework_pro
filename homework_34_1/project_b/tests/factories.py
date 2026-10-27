import factory

from warehouse.models import Shipment, ShipmentItem, StockItem, User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')


class StockItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockItem

    book_id = factory.Sequence(lambda n: n + 1)
    title = factory.Sequence(lambda n: f'Book {n}')
    quantity = 10


class ShipmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Shipment

    order_id = factory.Sequence(lambda n: n + 1)
    email = factory.Sequence(lambda n: f'buyer{n}@example.com')
    status = Shipment.STATUS_PENDING


class ShipmentItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShipmentItem

    shipment = factory.SubFactory(ShipmentFactory)
    book_id = factory.Sequence(lambda n: n + 1)
    title = 'Book'
    quantity = 1