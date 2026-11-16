
import pytest
from django.contrib.auth import get_user_model

Usuario = get_user_model()


@pytest.mark.django_db
def test_crear_cliente_por_defecto():
    usuario = Usuario.objects.create_user(
        username='cliente1',
        email='cliente@test.com',
        password='Test12345!'
    )

    assert usuario.rol == Usuario.Rol.CLIENTE
    assert usuario.email == 'cliente@test.com'
    assert usuario.check_password('Test12345!')


@pytest.mark.django_db
def test_crear_operario():
    usuario = Usuario.objects.create_user(
        username='operario1',
        email='operario@test.com',
        password='Test12345!',
        rol=Usuario.Rol.OPERARIO
    )

    assert usuario.rol == Usuario.Rol.OPERARIO


@pytest.mark.django_db
def test_crear_administrador():
    usuario = Usuario.objects.create_user(
        username='admin1',
        email='admin@test.com',
        password='Test12345!',
        rol=Usuario.Rol.ADMINISTRADOR
    )

    assert usuario.rol == Usuario.Rol.ADMINISTRADOR
