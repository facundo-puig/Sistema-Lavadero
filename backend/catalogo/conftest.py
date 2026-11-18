import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


def _crear_cliente(email):
    return get_user_model().objects.create_user(
        username=email,
        email=email,
        password='clave-de-prueba-123',
    )


@pytest.fixture
def cliente(db):
    return _crear_cliente('ana@example.com')


@pytest.fixture
def otro_cliente(db):
    return _crear_cliente('beto@example.com')


@pytest.fixture
def api_cliente(cliente):
    api = APIClient()
    api.force_authenticate(cliente)
    return api
