"""Tests de `POST /api/turnos/{id}/cancelar/`.

Necesitan Postgres.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogo.models import Servicio, Tarifa, TipoVehiculo
from turnos.estados import Estado

Usuario = get_user_model()

pytestmark = pytest.mark.django_db


def url(turno):
    return f'/api/turnos/{turno.id}/cancelar/'


def api_de(usuario):
    cliente_api = APIClient()
    cliente_api.force_authenticate(usuario)
    return cliente_api


@pytest.fixture
def api(cliente):
    return api_de(cliente)


@pytest.fixture
def otro_cliente(db):
    return Usuario.objects.create_user(
        username='beto@test.com', email='beto@test.com', password='Test12345!'
    )


@pytest.fixture
def usuario_admin(db):
    return Usuario.objects.create_user(
        username='admin@test.com',
        email='admin@test.com',
        password='Test12345!',
        rol=Usuario.Rol.ADMINISTRADOR,
    )


@pytest.fixture
def usuario_operario(db):
    return Usuario.objects.create_user(
        username='op@test.com',
        email='op@test.com',
        password='Test12345!',
        rol=Usuario.Rol.OPERARIO,
    )


def test_sin_sesion_da_401(crear_turno):
    turno = crear_turno()

    respuesta = APIClient().post(url(turno))

    assert respuesta.status_code == 401
    turno.refresh_from_db()
    assert turno.estado == Estado.PENDIENTE


def test_cliente_cancela_su_turno_pendiente(api, crear_turno):
    turno = crear_turno()

    respuesta = api.post(url(turno))

    assert respuesta.status_code == 200
    assert respuesta.data['estado'] == 'cancelado'
    assert respuesta.data['id'] == turno.id
    turno.refresh_from_db()
    assert turno.estado == Estado.CANCELADO


def test_la_respuesta_trae_el_turno_completo(api, crear_turno):
    turno = crear_turno()

    respuesta = api.post(url(turno))

    assert {'id', 'estado', 'inicio', 'fin', 'precio_total', 'box', 'vehiculo'} <= set(
        respuesta.data
    )


def test_cliente_no_puede_cancelar_el_turno_de_otro(otro_cliente, crear_turno):
    turno = crear_turno()

    respuesta = api_de(otro_cliente).post(url(turno))

    assert respuesta.status_code == 404
    turno.refresh_from_db()
    assert turno.estado == Estado.PENDIENTE


def test_turno_inexistente_da_404(api):
    respuesta = api.post('/api/turnos/999999/cancelar/')

    assert respuesta.status_code == 404


def test_administrador_cancela_cualquier_turno(usuario_admin, crear_turno):
    turno = crear_turno()

    respuesta = api_de(usuario_admin).post(url(turno))

    assert respuesta.status_code == 200
    turno.refresh_from_db()
    assert turno.estado == Estado.CANCELADO


def test_operario_cancela_cualquier_turno(usuario_operario, crear_turno):
    turno = crear_turno()

    respuesta = api_de(usuario_operario).post(url(turno))

    assert respuesta.status_code == 200
    turno.refresh_from_db()
    assert turno.estado == Estado.CANCELADO


@pytest.mark.parametrize(
    'estado',
    [Estado.EN_PROCESO, Estado.FINALIZADO, Estado.ENTREGADO, Estado.CANCELADO],
)
def test_solo_se_cancela_un_turno_pendiente(api, crear_turno, estado):
    turno = crear_turno(estado=estado)

    respuesta = api.post(url(turno))

    assert respuesta.status_code == 400
    assert respuesta.data == {'detail': 'Solo se puede cancelar un turno pendiente.'}
    turno.refresh_from_db()
    assert turno.estado == estado


def test_cancelar_dos_veces_da_400_la_segunda(api, crear_turno):
    turno = crear_turno()

    primera = api.post(url(turno))
    segunda = api.post(url(turno))

    assert primera.status_code == 200
    assert segunda.status_code == 400


def test_cancelar_libera_el_horario_para_otra_reserva(api, cliente, vehiculo, box_1, monkeypatch):
    """Punta a punta por la API: se reserva, se cancela y el mismo horario se vuelve a reservar."""
    monkeypatch.setattr(
        'django.utils.timezone.now', lambda: datetime(2026, 11, 16, 12, 0, tzinfo=UTC)
    )
    servicio = Servicio.objects.create(nombre='Lavado completo')
    Tarifa.objects.create(
        servicio=servicio,
        tipo_vehiculo=TipoVehiculo.AUTO,
        precio=Decimal('9000.00'),
        duracion_minutos=45,
    )
    pedido = {
        'vehiculo': vehiculo.id,
        'servicios': [servicio.id],
        'inicio': '2026-11-20T13:00:00Z',
    }

    primero = api.post('/api/turnos/', pedido, format='json')
    assert primero.status_code == 201
    # Con un solo box, el mismo horario está ocupado hasta que se cancele.
    assert api.post('/api/turnos/', pedido, format='json').status_code == 409

    assert api.post(f'/api/turnos/{primero.data["id"]}/cancelar/').status_code == 200

    segundo = api.post('/api/turnos/', pedido, format='json')
    assert segundo.status_code == 201
    assert segundo.data['box']['id'] == box_1.id


def test_no_se_permite_cancelar_con_get(api, crear_turno):
    turno = crear_turno()

    respuesta = api.get(url(turno))

    assert respuesta.status_code == 405