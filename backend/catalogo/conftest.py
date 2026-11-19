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


def _crear_con_rol(email, rol):
    return get_user_model().objects.create_user(
        username=email,
        email=email,
        password='clave-de-prueba-123',
        rol=rol,
    )


@pytest.fixture
def administrador(db):
    return _crear_con_rol('admin@example.com', get_user_model().Rol.ADMINISTRADOR)


@pytest.fixture
def operario(db):
    return _crear_con_rol('op@example.com', get_user_model().Rol.OPERARIO)


@pytest.fixture
def api_de():
    def _api(usuario):
        api = APIClient()
        api.force_authenticate(usuario)
        return api

    return _api
