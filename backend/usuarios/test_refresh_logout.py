
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


@pytest.mark.django_db
def test_logout_no_revoca_refresh_de_otro_usuario(usuario_prueba, tokens):
    Usuario = get_user_model()

    otro_usuario = Usuario.objects.create_user(
        username='otro@ejemplo.com',
        email='otro@ejemplo.com',
        password='Prueba12345!',
        rol=Usuario.Rol.CLIENTE,
    )

    cliente = APIClient()

    respuesta_login = cliente.post(
        '/api/auth/login/',
        {
            'email': otro_usuario.email,
            'password': 'Prueba12345!',
        },
        format='json',
    )

    assert respuesta_login.status_code == 200

    # El segundo usuario intenta revocar el refresh del primero.
    cliente.credentials(
        HTTP_AUTHORIZATION=f"Bearer {respuesta_login.data['access']}"
    )

    respuesta_logout = cliente.post(
        '/api/auth/logout/',
        {'refresh': tokens['refresh']},
        format='json',
    )

    assert respuesta_logout.status_code == 400
    assert 'refresh' in respuesta_logout.data

    # El refresh del primer usuario debe seguir funcionando.
    cliente.credentials()

    respuesta_refresh = cliente.post(
        '/api/auth/refresh/',
        {'refresh': tokens['refresh']},
        format='json',
    )

    assert respuesta_refresh.status_code == 200
    assert 'access' in respuesta_refresh.data
