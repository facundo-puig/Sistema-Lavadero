
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def cliente_api():
    return APIClient()


@pytest.fixture
def usuario_prueba(db):
    Usuario = get_user_model()

    return Usuario.objects.create_user(
        username='cliente@ejemplo.com',
        email='cliente@ejemplo.com',
        password='Prueba12345!',
        rol=Usuario.Rol.CLIENTE,
    )


def test_login_correcto(cliente_api, usuario_prueba):
    respuesta = cliente_api.post(
        '/api/auth/login/',
        {
            'email': 'cliente@ejemplo.com',
            'password': 'Prueba12345!',
        },
        format='json',
    )

    assert respuesta.status_code == 200
    assert 'access' in respuesta.data
    assert 'refresh' in respuesta.data
    assert respuesta.data['usuario']['rol'] == 'CLIENTE'
    assert respuesta.data['usuario']['email'] == usuario_prueba.email


def test_login_contrasena_incorrecta(cliente_api, usuario_prueba):
    respuesta = cliente_api.post(
        '/api/auth/login/',
        {
            'email': 'cliente@ejemplo.com',
            'password': 'Incorrecta123!',
        },
        format='json',
    )

    assert respuesta.status_code == 401
    assert 'access' not in respuesta.data


def test_login_usuario_inactivo(cliente_api, usuario_prueba):
    usuario_prueba.is_active = False
    usuario_prueba.save()

    respuesta = cliente_api.post(
        '/api/auth/login/',
        {
            'email': 'cliente@ejemplo.com',
            'password': 'Prueba12345!',
        },
        format='json',
    )

    assert respuesta.status_code == 401
    assert 'access' not in respuesta.data
