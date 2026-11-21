"""Tests de `GET /api/resumen/` (resumen de turnos e ingresos, solo administrador).

Necesitan Postgres.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from turnos.estados import Estado
from turnos.models import Turno

Usuario = get_user_model()
URL = '/api/resumen/'

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


@pytest.fixture
def crear(vehiculo, box_1, box_2):
    """Crea un turno con el estado, el precio y el inicio indicados.

    Alterna los boxes para que turnos a la misma hora no se superpongan en la base.
    """
    contador = {'n': 0}

    def _crear(inicio, estado=Estado.PENDIENTE, precio='1000.00'):
        contador['n'] += 1
        box = box_1 if contador['n'] % 2 else box_2
        return Turno.objects.create(
            vehiculo=vehiculo,
            box=box,
            inicio=inicio,
            fin=inicio + timedelta(minutes=30),
            estado=estado,
            precio_total=Decimal(precio),
        )

    return _crear


def utc(dia, hora=13, minuto=0, mes=11):
    return datetime(2026, mes, dia, hora, minuto, tzinfo=UTC)


def resumen(usuario, desde, hasta):
    return api_de(usuario).get(URL, {'desde': desde, 'hasta': hasta})


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


def test_sin_sesion_es_401():
    assert APIClient().get(URL, {'desde': '2026-11-01', 'hasta': '2026-11-30'}).status_code == 401


def test_el_cliente_no_puede_ver_el_resumen(cliente):
    assert resumen(cliente, '2026-11-01', '2026-11-30').status_code == 403


def test_el_operario_no_puede_ver_el_resumen(operario):
    assert resumen(operario, '2026-11-01', '2026-11-30').status_code == 403


def test_el_administrador_puede_ver_el_resumen(administrador):
    assert resumen(administrador, '2026-11-01', '2026-11-30').status_code == 200


# ---------------------------------------------------------------------------
# Cálculo
# ---------------------------------------------------------------------------


def test_cuenta_los_turnos_por_estado_y_suma_solo_los_finalizados_y_entregados(
    administrador, crear
):
    crear(utc(10, 12), Estado.PENDIENTE, '1000.00')
    crear(utc(10, 13), Estado.PENDIENTE, '1000.00')
    crear(utc(11, 12), Estado.EN_PROCESO, '2000.00')
    crear(utc(12, 12), Estado.FINALIZADO, '3000.50')
    crear(utc(13, 12), Estado.ENTREGADO, '4000.00')
    crear(utc(13, 13), Estado.ENTREGADO, '5000.25')
    crear(utc(14, 12), Estado.CANCELADO, '9999.00')

    respuesta = resumen(administrador, '2026-11-01', '2026-11-30')

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        'desde': '2026-11-01',
        'hasta': '2026-11-30',
        'turnos_por_estado': {
            'pendiente': 2,
            'en_proceso': 1,
            'finalizado': 1,
            'entregado': 2,
            'cancelado': 1,
        },
        'ingresos_total': '12000.75',
    }


def test_un_periodo_sin_turnos_devuelve_ceros(administrador):
    respuesta = resumen(administrador, '2026-11-01', '2026-11-30')

    assert respuesta.status_code == 200
    assert respuesta.json()['turnos_por_estado'] == {
        'pendiente': 0,
        'en_proceso': 0,
        'finalizado': 0,
        'entregado': 0,
        'cancelado': 0,
    }
    assert respuesta.json()['ingresos_total'] == '0.00'


def test_los_pendientes_en_proceso_y_cancelados_no_suman_ingresos(administrador, crear):
    crear(utc(10), Estado.PENDIENTE, '1000.00')
    crear(utc(11), Estado.EN_PROCESO, '1000.00')
    crear(utc(12), Estado.CANCELADO, '1000.00')

    assert resumen(administrador, '2026-11-01', '2026-11-30').json()['ingresos_total'] == '0.00'


def test_los_importes_viajan_con_dos_decimales(administrador, crear):
    crear(utc(10), Estado.ENTREGADO, '12500')

    assert resumen(administrador, '2026-11-01', '2026-11-30').json()['ingresos_total'] == '12500.00'


# ---------------------------------------------------------------------------
# Período (días en hora de Argentina, ambos extremos incluidos)
# ---------------------------------------------------------------------------


def test_desde_y_hasta_estan_incluidos(administrador, crear):
    crear(utc(1, 12), Estado.ENTREGADO, '100.00')  # primer día
    crear(utc(30, 12), Estado.ENTREGADO, '200.00')  # último día
    crear(utc(15, 12), Estado.ENTREGADO, '400.00')  # en el medio

    assert resumen(administrador, '2026-11-01', '2026-11-30').json()['ingresos_total'] == '700.00'


def test_los_turnos_fuera_del_periodo_no_cuentan(administrador, crear):
    crear(utc(31, 12, mes=10), Estado.ENTREGADO, '100.00')  # un día antes
    crear(utc(1, 12, mes=12), Estado.ENTREGADO, '200.00')  # un día después
    crear(utc(15, 12), Estado.ENTREGADO, '400.00')

    respuesta = resumen(administrador, '2026-11-01', '2026-11-30')

    assert respuesta.json()['ingresos_total'] == '400.00'
    assert respuesta.json()['turnos_por_estado']['entregado'] == 1


def test_el_borde_del_dia_es_el_de_argentina_no_el_de_utc(administrador, crear):
    # 1/12 02:59 UTC es el 30/11 a las 23:59 en Argentina: pertenece a noviembre.
    crear(datetime(2026, 12, 1, 2, 59, tzinfo=UTC), Estado.ENTREGADO, '100.00')
    # 1/12 03:00 UTC es el 1/12 a las 00:00 en Argentina: ya es diciembre.
    crear(datetime(2026, 12, 1, 3, 0, tzinfo=UTC), Estado.ENTREGADO, '200.00')
    # 1/11 02:59 UTC es el 31/10 a las 23:59 en Argentina: es octubre.
    crear(datetime(2026, 11, 1, 2, 59, tzinfo=UTC), Estado.ENTREGADO, '400.00')

    noviembre = resumen(administrador, '2026-11-01', '2026-11-30').json()

    assert noviembre['ingresos_total'] == '100.00'


def test_un_solo_dia_con_desde_igual_a_hasta(administrador, crear):
    crear(utc(10, 12), Estado.ENTREGADO, '100.00')
    crear(utc(11, 12), Estado.ENTREGADO, '200.00')

    respuesta = resumen(administrador, '2026-11-10', '2026-11-10')

    assert respuesta.status_code == 200
    assert respuesta.json()['ingresos_total'] == '100.00'


# ---------------------------------------------------------------------------
# Datos inválidos
# ---------------------------------------------------------------------------


def test_falta_desde_y_hasta_es_400(administrador):
    respuesta = api_de(administrador).get(URL)

    assert respuesta.status_code == 400
    assert 'desde' in respuesta.json()
    assert 'hasta' in respuesta.json()


@pytest.mark.parametrize('faltante', ['desde', 'hasta'])
def test_falta_un_parametro_es_400(administrador, faltante):
    parametros = {'desde': '2026-11-01', 'hasta': '2026-11-30'}
    del parametros[faltante]

    respuesta = api_de(administrador).get(URL, parametros)

    assert respuesta.status_code == 400
    assert faltante in respuesta.json()


@pytest.mark.parametrize('valor', ['hoy', '2026-13-45', '01/11/2026', '2026-11'])
def test_una_fecha_con_formato_invalido_es_400(administrador, valor):
    respuesta = resumen(administrador, valor, '2026-11-30')

    assert respuesta.status_code == 400
    assert 'desde' in respuesta.json()


def test_desde_posterior_a_hasta_es_400(administrador):
    respuesta = resumen(administrador, '2026-11-30', '2026-11-01')

    assert respuesta.status_code == 400
    assert 'posterior' in respuesta.json()['desde'][0]


def test_los_mensajes_estan_en_espanol(administrador):
    respuesta = api_de(administrador).get(URL, {'hasta': 'mañana'})

    assert 'Indicá la fecha desde' in respuesta.json()['desde'][0]
    assert 'Fecha inválida' in respuesta.json()['hasta'][0]


# ---------------------------------------------------------------------------
# Rendimiento y documentación
# ---------------------------------------------------------------------------


def test_el_resumen_usa_pocas_consultas(administrador, crear, django_assert_max_num_queries):
    for dia in range(1, 11):
        crear(utc(dia, 12), Estado.ENTREGADO)

    with django_assert_max_num_queries(2):
        resumen(administrador, '2026-11-01', '2026-11-30')


def test_el_endpoint_aparece_en_la_documentacion(administrador):
    respuesta = api_de(administrador).get('/api/schema/', {'format': 'json'})

    assert '/api/resumen/' in respuesta.json()['paths']