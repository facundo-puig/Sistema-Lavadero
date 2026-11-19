"""Quién puede usar cada endpoint de turnos (matriz de `docs/permisos-roles.md`).

Necesitan Postgres.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

Usuario = get_user_model()

pytestmark = pytest.mark.django_db


def api_de(usuario):
    cliente_api = APIClient()
    cliente_api.force_authenticate(usuario)
    return cliente_api


@pytest.fixture
def administrador(db):
    return Usuario.objects.create_user(
        username='admin@test.com',
        email='admin@test.com',
        password='Test12345!',
        rol=Usuario.Rol.ADMINISTRADOR,
    )


@pytest.fixture
def operario(db):
    return Usuario.objects.create_user(
        username='op@test.com',
        email='op@test.com',
        password='Test12345!',
        rol=Usuario.Rol.OPERARIO,
    )


@pytest.mark.parametrize('rol', ['administrador', 'operario'])
def test_administrador_y_operario_no_pueden_reservar(request, rol, vehiculo):
    usuario = request.getfixturevalue(rol)
    pedido = {'vehiculo': vehiculo.id, 'servicios': [1], 'inicio': '2026-12-10T13:00:00Z'}

    respuesta = api_de(usuario).post('/api/turnos/', pedido, format='json')

    assert respuesta.status_code == 403


@pytest.mark.parametrize('rol', ['administrador', 'operario'])
def test_el_personal_ve_el_listado_y_el_detalle(request, rol, crear_turno):
    usuario = request.getfixturevalue(rol)
    turno = crear_turno()

    assert api_de(usuario).get('/api/turnos/').status_code == 200
    assert api_de(usuario).get(f'/api/turnos/{turno.id}/').status_code == 200


def test_el_cliente_no_puede_cambiar_el_estado(cliente, crear_turno):
    turno = crear_turno()

    respuesta = api_de(cliente).patch(
        f'/api/turnos/{turno.id}/estado/', {'estado': 'en_proceso'}, format='json'
    )

    assert respuesta.status_code == 403