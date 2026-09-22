import pytest

from .factories import (
    BookFactory,
    CategoryFactory,
    OrderFactory,
)


@pytest.mark.django_db
def test_category_str_generated_with_ai():
    # Generated with AI, reviewed and modified
    category = CategoryFactory(name='Python')

    assert str(category) == 'Python'


@pytest.mark.django_db
def test_category_slug_generated_with_ai():
    # Generated with AI, reviewed and modified
    category = CategoryFactory(
        name='Django',
        slug='django'
    )

    assert category.name == 'Django'
    assert category.slug == 'django'


@pytest.mark.django_db
def test_book_str_generated_with_ai():
    # Generated with AI, reviewed and modified
    book = BookFactory(title='Django')

    assert str(book) == 'Django'


@pytest.mark.django_db
def test_book_fields_generated_with_ai():
    # Generated with AI, reviewed and modified
    book = BookFactory(
        title='Python',
        author='Guido van Rossum',
        stock=15
    )

    assert book.title == 'Python'
    assert book.author == 'Guido van Rossum'
    assert book.stock == 15


@pytest.mark.django_db
def test_order_str_generated_with_ai():
    # Generated with AI, reviewed and modified
    order = OrderFactory()

    assert str(order) == f'Замовлення #{order.pk}'


@pytest.mark.django_db
def test_order_default_status_generated_with_ai():
    # Generated with AI, reviewed and modified
    order = OrderFactory()

    assert order.status == OrderFactory._meta.model.STATUS_PENDING