"""Tests de `PATCH /api/turnos/{id}/estado/`.

Necesitan Postgres.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from turnos.estados import Estado

Usuario = get_user_model()

pytestmark = pytest.mark.django_db


def url(turno):
    return f'/api/turnos/{turno.id}/estado/'


def api_de(usuario):
    cliente_api = APIClient()
    cliente_api.force_authenticate(usuario)
    return cliente_api


@pytest.fixture
def operario(db):
    return Usuario.objects.create_user(
        username='op@test.com',
        email='op@test.com',
        password='Test12345!',
        rol=Usuario.Rol.OPERARIO,
    )


@pytest.fixture
def administrador(db):
    return Usuario.objects.create_user(
        username='admin@test.com',
        email='admin@test.com',
        password='Test12345!',
        rol=Usuario.Rol.ADMINISTRADOR,
    )


def test_sin_sesion_da_401(crear_turno):
    turno = crear_turno()

    respuesta = APIClient().patch(url(turno), {'estado': 'en_proceso'}, format='json')

    assert respuesta.status_code == 401


def test_el_cliente_no_puede_cambiar_el_estado(cliente, crear_turno):
    turno = crear_turno()

    respuesta = api_de(cliente).patch(url(turno), {'estado': 'en_proceso'}, format='json')

    assert respuesta.status_code == 403
    turno.refresh_from_db()
    assert turno.estado == Estado.PENDIENTE


@pytest.mark.parametrize(
    ('actual', 'nuevo'),
    [
        (Estado.PENDIENTE, Estado.EN_PROCESO),
        (Estado.EN_PROCESO, Estado.FINALIZADO),
        (Estado.FINALIZADO, Estado.ENTREGADO),
    ],
)
def test_el_operario_avanza_un_paso_del_flujo(operario, crear_turno, actual, nuevo):
    turno = crear_turno(estado=actual)

    respuesta = api_de(operario).patch(url(turno), {'estado': nuevo.value}, format='json')

    assert respuesta.status_code == 200
    assert respuesta.data['estado'] == nuevo.value
    turno.refresh_from_db()
    assert turno.estado == nuevo


def test_el_administrador_tambien_puede(administrador, crear_turno):
    turno = crear_turno()

    respuesta = api_de(administrador).patch(url(turno), {'estado': 'en_proceso'}, format='json')

    assert respuesta.status_code == 200


def test_la_respuesta_trae_el_turno_completo(operario, crear_turno):
    turno = crear_turno()

    respuesta = api_de(operario).patch(url(turno), {'estado': 'en_proceso'}, format='json')

    assert {'id', 'estado', 'inicio', 'fin', 'precio_total', 'box', 'vehiculo'} <= set(
        respuesta.data
    )


@pytest.mark.parametrize(
    ('actual', 'nuevo'),
    [
        (Estado.PENDIENTE, Estado.FINALIZADO),
        (Estado.PENDIENTE, Estado.ENTREGADO),
        (Estado.EN_PROCESO, Estado.PENDIENTE),
        (Estado.EN_PROCESO, Estado.ENTREGADO),
        (Estado.FINALIZADO, Estado.EN_PROCESO),
        (Estado.ENTREGADO, Estado.FINALIZADO),
        (Estado.PENDIENTE, Estado.PENDIENTE),
    ],
)
def test_no_se_puede_saltar_ni_retroceder(operario, crear_turno, actual, nuevo):
    turno = crear_turno(estado=actual)

    respuesta = api_de(operario).patch(url(turno), {'estado': nuevo.value}, format='json')

    assert respuesta.status_code == 400
    assert 'estado' in respuesta.data
    turno.refresh_from_db()
    assert turno.estado == actual


@pytest.mark.parametrize('actual', [Estado.ENTREGADO, Estado.CANCELADO])
def test_un_turno_terminado_no_admite_cambios(operario, crear_turno, actual):
    turno = crear_turno(estado=actual)

    respuesta = api_de(operario).patch(url(turno), {'estado': 'en_proceso'}, format='json')

    assert respuesta.status_code == 400


def test_cancelar_por_aca_da_400_y_explica_que_hay_otro_endpoint(operario, crear_turno):
    turno = crear_turno()

    respuesta = api_de(operario).patch(url(turno), {'estado': 'cancelado'}, format='json')

    assert respuesta.status_code == 400
    assert 'cancelación' in respuesta.data['estado'][0]
    turno.refresh_from_db()
    assert turno.estado == Estado.PENDIENTE


def test_estado_inexistente_da_400(operario, crear_turno):
    turno = crear_turno()

    respuesta = api_de(operario).patch(url(turno), {'estado': 'volando'}, format='json')

    assert respuesta.status_code == 400
    assert 'estado' in respuesta.data


def test_sin_estado_en_el_cuerpo_da_400(operario, crear_turno):
    turno = crear_turno()

    respuesta = api_de(operario).patch(url(turno), {}, format='json')

    assert respuesta.status_code == 400
    assert 'estado' in respuesta.data


def test_turno_inexistente_da_404(operario):
    respuesta = api_de(operario).patch(
        '/api/turnos/999999/estado/', {'estado': 'en_proceso'}, format='json'
    )

    assert respuesta.status_code == 404


def test_recorre_el_flujo_completo(operario, crear_turno):
    turno = crear_turno()
    api = api_de(operario)

    for estado in ('en_proceso', 'finalizado', 'entregado'):
        assert api.patch(url(turno), {'estado': estado}, format='json').status_code == 200

    turno.refresh_from_db()
    assert turno.estado == Estado.ENTREGADO