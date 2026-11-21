"""Tests de `GET /api/turnos/` y `GET /api/turnos/{id}/` (Mis turnos).

Necesitan Postgres.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogo.models import Servicio, TipoVehiculo, Vehiculo
from turnos.estados import Estado
from turnos.models import Turno, TurnoServicio

Usuario = get_user_model()
URL = '/api/turnos/'

pytestmark = pytest.mark.django_db


def inicio_del_dia(dia, hora=13):
    return datetime(2026, 11, dia, hora, 0, tzinfo=UTC)


@pytest.fixture
def api(cliente):
    cliente_api = APIClient()
    cliente_api.force_authenticate(cliente)
    return cliente_api


@pytest.fixture
def otro_cliente(db):
    return Usuario.objects.create_user(
        username='beto@test.com', email='beto@test.com', password='Test12345!'
    )


@pytest.fixture
def vehiculo_de_otro(otro_cliente):
    return Vehiculo.objects.create(
        cliente=otro_cliente, patente='ZZ999ZZ', tipo=TipoVehiculo.CAMIONETA
    )


@pytest.fixture
def crear(box_1):
    """Crea un turno en la base para el vehículo indicado, el día del mes indicado."""

    def _crear(vehiculo, dia=20, hora=13, estado=Estado.PENDIENTE):
        inicio = inicio_del_dia(dia, hora)
        return Turno.objects.create(
            vehiculo=vehiculo,
            box=box_1,
            inicio=inicio,
            fin=inicio + timedelta(minutes=45),
            estado=estado,
            precio_total=Decimal('9000.00'),
        )

    return _crear


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------


def test_el_listado_sin_sesion_es_401():
    assert APIClient().get(URL).status_code == 401


def test_el_detalle_sin_sesion_es_401(crear, vehiculo):
    turno = crear(vehiculo)

    assert APIClient().get(f'{URL}{turno.id}/').status_code == 401


# ---------------------------------------------------------------------------
# Regla 5: un cliente solo ve lo suyo
# ---------------------------------------------------------------------------


def test_el_cliente_lista_solo_sus_turnos(api, crear, vehiculo, vehiculo_de_otro):
    propio = crear(vehiculo, dia=20)
    crear(vehiculo_de_otro, dia=21)

    respuesta = api.get(URL)

    assert respuesta.status_code == 200
    assert respuesta.json()['count'] == 1
    assert [t['id'] for t in respuesta.json()['results']] == [propio.id]


def test_un_cliente_sin_turnos_recibe_una_lista_vacia(api, crear, vehiculo_de_otro):
    crear(vehiculo_de_otro)

    respuesta = api.get(URL)

    assert respuesta.status_code == 200
    assert respuesta.json() == {'count': 0, 'next': None, 'previous': None, 'results': []}


def test_el_detalle_de_un_turno_propio_es_200(api, crear, vehiculo):
    turno = crear(vehiculo)

    respuesta = api.get(f'{URL}{turno.id}/')

    assert respuesta.status_code == 200
    assert respuesta.json()['id'] == turno.id


def test_el_detalle_de_un_turno_ajeno_es_404(api, crear, vehiculo_de_otro):
    ajeno = crear(vehiculo_de_otro)

    assert api.get(f'{URL}{ajeno.id}/').status_code == 404


def test_el_detalle_de_un_turno_inexistente_es_404(api):
    assert api.get(f'{URL}99999/').status_code == 404


@pytest.mark.parametrize('rol', [Usuario.Rol.ADMINISTRADOR, Usuario.Rol.OPERARIO])
def test_administrador_y_operario_ven_los_turnos_de_todos(
    crear, vehiculo, vehiculo_de_otro, rol
):
    crear(vehiculo, dia=20)
    ajeno = crear(vehiculo_de_otro, dia=21)
    personal = Usuario.objects.create_user(
        username='staff@test.com', email='staff@test.com', password='Test12345!', rol=rol
    )
    api_personal = APIClient()
    api_personal.force_authenticate(personal)

    assert api_personal.get(URL).json()['count'] == 2
    assert api_personal.get(f'{URL}{ajeno.id}/').status_code == 200


# ---------------------------------------------------------------------------
# Forma de la respuesta, orden y paginación
# ---------------------------------------------------------------------------


def test_el_turno_tiene_la_forma_del_contrato(api, crear, vehiculo, box_1):
    turno = crear(vehiculo)
    lavado = Servicio.objects.create(nombre='Lavado completo')
    encerado = Servicio.objects.create(nombre='Encerado')
    TurnoServicio.objects.create(
        turno=turno, servicio=lavado, precio=Decimal('9000.00'), duracion_minutos=45
    )
    TurnoServicio.objects.create(
        turno=turno, servicio=encerado, precio=Decimal('3500.00'), duracion_minutos=30
    )

    respuesta = api.get(f'{URL}{turno.id}/')

    assert respuesta.json() == {
        'id': turno.id,
        'vehiculo': {'id': vehiculo.id, 'patente': 'AB123CD', 'tipo': 'auto'},
        'box': {'id': box_1.id, 'nombre': 'Box 1'},
        'inicio': '2026-11-20T13:00:00Z',
        'fin': '2026-11-20T13:45:00Z',
        'estado': 'pendiente',
        'precio_total': '9000.00',
        'servicios': [
            {'id': lavado.id, 'nombre': 'Lavado completo', 'precio_aplicado': '9000.00'},
            {'id': encerado.id, 'nombre': 'Encerado', 'precio_aplicado': '3500.00'},
        ],
    }


def test_los_turnos_vienen_ordenados_por_inicio(api, crear, vehiculo):
    tercero = crear(vehiculo, dia=25)
    primero = crear(vehiculo, dia=18)
    segundo = crear(vehiculo, dia=22)

    ids = [t['id'] for t in api.get(URL).json()['results']]

    assert ids == [primero.id, segundo.id, tercero.id]


def test_el_listado_incluye_los_turnos_cancelados_y_entregados(api, crear, vehiculo):
    crear(vehiculo, dia=18, estado=Estado.CANCELADO)
    crear(vehiculo, dia=19, estado=Estado.ENTREGADO)

    estados = [t['estado'] for t in api.get(URL).json()['results']]

    assert estados == ['cancelado', 'entregado']


def test_el_listado_se_pagina_de_a_20(api, crear, vehiculo):
    for dia in range(1, 26):  # 25 turnos, uno por día de noviembre
        crear(vehiculo, dia=dia)

    pagina_1 = api.get(URL).json()
    pagina_2 = api.get(URL, {'page': 2}).json()

    assert pagina_1['count'] == 25
    assert len(pagina_1['results']) == 20
    assert pagina_1['next'] is not None
    assert pagina_1['previous'] is None
    assert len(pagina_2['results']) == 5
    assert pagina_2['next'] is None


def test_la_cantidad_de_consultas_no_crece_con_los_turnos(
    api, crear, vehiculo, django_assert_max_num_queries
):
    servicio = Servicio.objects.create(nombre='Lavado completo')
    for dia in range(1, 11):
        turno = crear(vehiculo, dia=dia)
        TurnoServicio.objects.create(
            turno=turno, servicio=servicio, precio=Decimal('9000.00'), duracion_minutos=45
        )

    with django_assert_max_num_queries(5):
        respuesta = api.get(URL)

    assert respuesta.status_code == 200
    assert len(respuesta.json()['results']) == 10