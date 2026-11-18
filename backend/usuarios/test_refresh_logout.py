
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def usuario_prueba(db):
    Usuario = get_user_model()

    return Usuario.objects.create_user(
        username='cliente@ejemplo.com',
        email='cliente@ejemplo.com',
        password='Prueba12345!',
        rol=Usuario.Rol.CLIENTE,
    )


@pytest.fixture
def tokens(usuario_prueba):
    cliente = APIClient()

    respuesta = cliente.post(
        '/api/auth/login/',
        {
            'email': 'cliente@ejemplo.com',
            'password': 'Prueba12345!',
        },
        format='json',
    )

    assert respuesta.status_code == 200
    return respuesta.data


def test_refresh_correcto(tokens):
    cliente = APIClient()

    respuesta = cliente.post(
        '/api/auth/refresh/',
        {'refresh': tokens['refresh']},
        format='json',
    )

    assert respuesta.status_code == 200
    assert 'access' in respuesta.data


def test_refresh_invalido(db):
    cliente = APIClient()

    respuesta = cliente.post(
        '/api/auth/refresh/',
        {'refresh': 'token_invalido'},
        format='json',
    )

    assert respuesta.status_code == 401


def test_logout_correcto(tokens):
    cliente = APIClient()
    cliente.credentials(
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
    )

    respuesta = cliente.post(
        '/api/auth/logout/',
        {'refresh': tokens['refresh']},
        format='json',
    )

    assert respuesta.status_code == 204

    cliente.credentials()

    respuesta_refresh = cliente.post(
        '/api/auth/refresh/',
        {'refresh': tokens['refresh']},
        format='json',
    )

    assert respuesta_refresh.status_code == 401


def test_logout_sin_autenticacion(tokens):
    cliente = APIClient()

    respuesta = cliente.post(
        '/api/auth/logout/',
        {'refresh': tokens['refresh']},
        format='json',
    )

    assert respuesta.status_code == 401
