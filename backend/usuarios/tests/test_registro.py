
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

Usuario = get_user_model()

URL_REGISTRO = '/api/auth/registro/'


@pytest.fixture
def cliente_api():
    return APIClient()


@pytest.mark.django_db
def test_registro_cliente_correcto(cliente_api):
    datos = {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'password': 'ClaveSegura123!',
    }

    respuesta = cliente_api.post(URL_REGISTRO, datos, format='json')

    assert respuesta.status_code == 201
    assert respuesta.data['nombre'] == 'Juan'
    assert respuesta.data['email'] == 'juan@test.com'
    assert respuesta.data['rol'] == 'CLIENTE'
    assert 'password' not in respuesta.data

    usuario = Usuario.objects.get(email='juan@test.com')
    assert usuario.check_password('ClaveSegura123!')


@pytest.mark.django_db
def test_registro_email_duplicado(cliente_api):
    Usuario.objects.create_user(
        username='juan@test.com',
        email='juan@test.com',
        password='ClaveSegura123!',
    )

    datos = {
        'nombre': 'Otro Juan',
        'email': 'juan@test.com',
        'password': 'OtraClave123!',
    }

    respuesta = cliente_api.post(URL_REGISTRO, datos, format='json')

    assert respuesta.status_code == 400
    assert 'email' in respuesta.data
    assert Usuario.objects.filter(email='juan@test.com').count() == 1


@pytest.mark.django_db
def test_registro_password_debil(cliente_api):
    datos = {
        'nombre': 'Pedro',
        'email': 'pedro@test.com',
        'password': '123',
    }

    respuesta = cliente_api.post(URL_REGISTRO, datos, format='json')

    assert respuesta.status_code == 400
    assert 'password' in respuesta.data
    assert not Usuario.objects.filter(email='pedro@test.com').exists()


@pytest.mark.django_db
def test_registro_no_permite_elegir_rol(cliente_api):
    datos = {
        'nombre': 'Carlos',
        'email': 'carlos@test.com',
        'password': 'ClaveSegura123!',
        'rol': 'ADMINISTRADOR',
    }

    respuesta = cliente_api.post(URL_REGISTRO, datos, format='json')

    assert respuesta.status_code == 201
    assert respuesta.data['rol'] == 'CLIENTE'

    usuario = Usuario.objects.get(email='carlos@test.com')
    assert usuario.rol == Usuario.Rol.CLIENTE
