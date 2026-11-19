"""Tests de la agenda: `GET /api/turnos/` para administrador y operario, con el cliente
incluido y los filtros `fecha`, `box` y `estado`.

Necesitan Postgres.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogo.models import TipoVehiculo, Vehiculo
from turnos.estados import Estado
from turnos.models import Turno

Usuario = get_user_model()
URL = '/api/turnos/'

pytestmark = pytest.mark.django_db


def api_de(usuario):
    cliente_api = APIClient()
    cliente_api.force_authenticate(usuario)
    return cliente_api


def ids(respuesta):
    return [turno['id'] for turno in respuesta.json()['results']]


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


@pytest.fixture
def beto(db):
    return Usuario.objects.create_user(
        username='beto@test.com',
        email='beto@test.com',
        password='Test12345!',
        first_name='Beto',
        last_name='Paz',
    )


@pytest.fixture
def vehiculo_de_beto(beto):
    return Vehiculo.objects.create(cliente=beto, patente='ZZ999ZZ', tipo=TipoVehiculo.CAMIONETA)


@pytest.fixture
def crear(vehiculo, box_1):
    """Crea un turno en la base con el inicio indicado (45 minutos de duración)."""

    def _crear(inicio, vehiculo_del_turno=None, box=None, estado=Estado.PENDIENTE):
        return Turno.objects.create(
            vehiculo=vehiculo_del_turno or vehiculo,
            box=box or box_1,
            inicio=inicio,
            fin=inicio + timedelta(minutes=45),
            estado=estado,
            precio_total=Decimal('9000.00'),
        )

    return _crear


def utc(dia, hora, minuto=0, mes=11):
    return datetime(2026, mes, dia, hora, minuto, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Quién ve qué
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('rol', ['administrador', 'operario'])
def test_el_personal_ve_los_turnos_de_todos_los_clientes(
    request, rol, crear, vehiculo_de_beto
):
    usuario = request.getfixturevalue(rol)
    de_ana = crear(utc(20, 13))
    de_beto = crear(utc(20, 14), vehiculo_del_turno=vehiculo_de_beto)

    respuesta = api_de(usuario).get(URL)

    assert respuesta.status_code == 200
    assert ids(respuesta) == [de_ana.id, de_beto.id]


def test_el_personal_ve_el_cliente_de_cada_turno(operario, crear, cliente, vehiculo_de_beto, beto):
    crear(utc(20, 13))
    crear(utc(20, 14), vehiculo_del_turno=vehiculo_de_beto)

    resultados = api_de(operario).get(URL).json()['results']

    # Ana no tiene nombre cargado: se muestra el email. Beto tiene nombre y apellido.
    assert resultados[0]['cliente'] == {'id': cliente.id, 'nombre': 'ana@test.com'}
    assert resultados[1]['cliente'] == {'id': beto.id, 'nombre': 'Beto Paz'}


def test_el_detalle_tambien_trae_el_cliente_para_el_personal(administrador, crear, cliente):
    turno = crear(utc(20, 13))

    respuesta = api_de(administrador).get(f'{URL}{turno.id}/')

    assert respuesta.status_code == 200
    assert respuesta.json()['cliente']['id'] == cliente.id


def test_el_cliente_ve_solo_sus_turnos_y_sin_el_campo_cliente(
    cliente, crear, vehiculo_de_beto
):
    propio = crear(utc(20, 13))
    crear(utc(20, 14), vehiculo_del_turno=vehiculo_de_beto)

    respuesta = api_de(cliente).get(URL)

    assert ids(respuesta) == [propio.id]
    assert 'cliente' not in respuesta.json()['results'][0]


def test_los_filtros_no_dejan_al_cliente_ver_turnos_ajenos(cliente, crear, vehiculo_de_beto, box_1):
    crear(utc(20, 14), vehiculo_del_turno=vehiculo_de_beto)

    respuesta = api_de(cliente).get(URL, {'fecha': '2026-11-20', 'box': box_1.id})

    assert respuesta.json()['results'] == []


def test_sin_sesion_es_401():
    assert APIClient().get(URL, {'fecha': '2026-11-20'}).status_code == 401


# ---------------------------------------------------------------------------
# Filtro por fecha (el día es el de Argentina, UTC-3)
# ---------------------------------------------------------------------------


def test_filtra_por_el_dia_en_hora_de_argentina(operario, crear, box_1, box_2):
    # Los turnos pegados al borde del día van en boxes distintos para que no se superpongan.
    antes = crear(utc(20, 2, 59), box=box_1)  # 19/11 23:59 en Argentina
    primero = crear(utc(20, 3, 0), box=box_2)  # 20/11 00:00 en Argentina
    ultimo = crear(utc(21, 2, 59), box=box_1)  # 20/11 23:59 en Argentina
    despues = crear(utc(21, 3, 0), box=box_2)  # 21/11 00:00 en Argentina

    del_20 = api_de(operario).get(URL, {'fecha': '2026-11-20'})
    del_19 = api_de(operario).get(URL, {'fecha': '2026-11-19'})
    del_21 = api_de(operario).get(URL, {'fecha': '2026-11-21'})

    assert ids(del_20) == [primero.id, ultimo.id]
    assert ids(del_19) == [antes.id]
    assert ids(del_21) == [despues.id]


def test_un_dia_sin_turnos_devuelve_la_lista_vacia(operario, crear):
    crear(utc(20, 13))

    respuesta = api_de(operario).get(URL, {'fecha': '2026-11-25'})

    assert respuesta.status_code == 200
    assert respuesta.json()['results'] == []
    assert respuesta.json()['count'] == 0


def test_el_cambio_de_mes_y_de_anio_se_respeta(operario, crear):
    fin_de_anio = crear(datetime(2027, 1, 1, 2, 30, tzinfo=UTC))  # 31/12/2026 23:30 en Argentina

    respuesta = api_de(operario).get(URL, {'fecha': '2026-12-31'})

    assert ids(respuesta) == [fin_de_anio.id]


# ---------------------------------------------------------------------------
# Filtros por box y por estado
# ---------------------------------------------------------------------------


def test_filtra_por_box(operario, crear, box_1, box_2):
    en_box_1 = crear(utc(20, 13), box=box_1)
    en_box_2 = crear(utc(20, 13), box=box_2)

    assert ids(api_de(operario).get(URL, {'box': box_1.id})) == [en_box_1.id]
    assert ids(api_de(operario).get(URL, {'box': box_2.id})) == [en_box_2.id]


def test_un_box_inexistente_devuelve_lista_vacia(operario, crear):
    crear(utc(20, 13))

    respuesta = api_de(operario).get(URL, {'box': 9999})

    assert respuesta.status_code == 200
    assert respuesta.json()['results'] == []


@pytest.mark.parametrize('estado', [e.value for e in Estado])
def test_filtra_por_cada_estado(operario, crear, estado):
    for hora, otro in enumerate(Estado):
        crear(utc(20, 8 + hora), estado=otro)

    resultados = api_de(operario).get(URL, {'estado': estado}).json()['results']

    assert len(resultados) == 1
    assert resultados[0]['estado'] == estado


def test_los_filtros_se_combinan(operario, crear, box_1, box_2):
    buscado = crear(utc(20, 13), box=box_1, estado=Estado.EN_PROCESO)
    crear(utc(20, 14), box=box_2, estado=Estado.EN_PROCESO)  # otro box
    crear(utc(20, 15), box=box_1, estado=Estado.PENDIENTE)  # otro estado
    crear(utc(22, 13), box=box_1, estado=Estado.EN_PROCESO)  # otro día

    respuesta = api_de(operario).get(
        URL, {'fecha': '2026-11-20', 'box': box_1.id, 'estado': 'en_proceso'}
    )

    assert ids(respuesta) == [buscado.id]


def test_sin_filtros_devuelve_todo_ordenado_por_inicio(operario, crear):
    tarde = crear(utc(21, 18))
    temprano = crear(utc(20, 9))
    medio = crear(utc(20, 15))

    assert ids(api_de(operario).get(URL)) == [temprano.id, medio.id, tarde.id]


# ---------------------------------------------------------------------------
# Filtros inválidos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('parametro', 'valor'),
    [
        ('fecha', 'hoy'),
        ('fecha', '2026-13-45'),
        ('fecha', '20/11/2026'),
        ('estado', 'volando'),
        ('estado', 'PENDIENTE'),
        ('box', 'uno'),
        ('box', '1.5'),
    ],
)
def test_un_filtro_invalido_es_400_y_marca_el_campo(operario, crear, parametro, valor):
    crear(utc(20, 13))

    respuesta = api_de(operario).get(URL, {parametro: valor})

    assert respuesta.status_code == 400
    assert parametro in respuesta.json()


def test_los_mensajes_de_filtros_invalidos_estan_en_espanol(operario):
    api = api_de(operario)

    assert 'Fecha inválida' in api.get(URL, {'fecha': 'hoy'}).json()['fecha'][0]
    assert 'no es un estado válido' in api.get(URL, {'estado': 'volando'}).json()['estado'][0]
    assert 'tiene que ser un número' in api.get(URL, {'box': 'uno'}).json()['box'][0]


def test_un_filtro_vacio_se_ignora(operario, crear):
    turno = crear(utc(20, 13))

    respuesta = api_de(operario).get(URL, {'fecha': '', 'box': '', 'estado': ''})

    assert respuesta.status_code == 200
    assert ids(respuesta) == [turno.id]


# ---------------------------------------------------------------------------
# Rendimiento y documentación
# ---------------------------------------------------------------------------


def test_la_agenda_no_hace_una_consulta_por_turno(
    operario, crear, vehiculo_de_beto, django_assert_max_num_queries
):
    for hora in range(8):
        crear(utc(20, 8 + hora), vehiculo_del_turno=vehiculo_de_beto if hora % 2 else None)

    with django_assert_max_num_queries(6):
        respuesta = api_de(operario).get(URL, {'fecha': '2026-11-20'})

    assert len(respuesta.json()['results']) == 8


def test_los_filtros_aparecen_en_la_documentacion(operario):
    respuesta = api_de(operario).get('/api/schema/', {'format': 'json'})

    assert respuesta.status_code == 200
    parametros = [
        p['name'] for p in respuesta.json()['paths']['/api/turnos/']['get']['parameters']
    ]
    assert {'fecha', 'box', 'estado'} <= set(parametros)