import pytest
from django.core.cache import cache
from .factories import (
    BookFactory,
    CategoryFactory,
    UserFactory,
)


@pytest.fixture(autouse=True)
def clear_test_cache():
    cache.clear()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def category():
    return CategoryFactory()


@pytest.fixture
def book():
    return BookFactory()


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client
