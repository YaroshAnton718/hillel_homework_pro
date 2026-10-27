import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache
from rest_framework.test import APIClient

from warehouse.apps import INTEGRATION_GROUP, MANAGERS_GROUP

from .factories import UserFactory


def make_client(user=None):
    client = APIClient()

    if user is not None:
        client.force_authenticate(user=user)

    return client


def user_in_group(group_name):
    user = UserFactory()
    user.groups.add(Group.objects.get(name=group_name))
    return user


@pytest.fixture(autouse=True)
def clear_test_cache():
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_client(db):
    return make_client(UserFactory())


@pytest.fixture
def service_client(db):
    return make_client(user_in_group(INTEGRATION_GROUP))


@pytest.fixture
def manager_client(db):
    return make_client(user_in_group(MANAGERS_GROUP))