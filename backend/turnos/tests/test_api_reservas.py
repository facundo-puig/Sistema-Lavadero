"""Tests de `POST /api/turnos/` (reserva de un turno).

Necesitan Postgres. La hora actual se fija en el 16/11/2026 12:00 UTC, así los tests
no dependen del día en que se corran.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogo.models import Box, Servicio, Tarifa, TipoVehiculo, Vehiculo
from turnos import reservas
from turnos.estados import Estado
from turnos.models import Turno, TurnoServicio

Usuario = get_user_model()
URL = '/api/turnos/'
AHORA = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def hora_actual_fija(monkeypatch):
    monkeypatch.setattr('django.utils.timezone.now', lambda: AHORA)


@pytest.fixture
def api(cliente):
    cliente_api = APIClient()
    cliente_api.force_authenticate(cliente)
    return cliente_api


@pytest.fixture
def lavado(db):
    servicio = Servicio.objects.create(nombre='Lavado completo')
    Tarifa.objects.create(
        servicio=servicio, tipo_vehiculo=TipoVehiculo.AUTO,
        precio=Decimal('9000.00'), duracion_minutos=45,
    )
    return servicio


@pytest.fixture
def encerado(db):
    """Tiene tarifa para auto, pero no para moto."""
    servicio = Servicio.objects.create(nombre='Encerado')
    Tarifa.objects.create(
        servicio=servicio, tipo_vehiculo=TipoVehiculo.AUTO,
        precio=Decimal('3500.00'), duracion_minutos=30,
    )
    return servicio


def pedido(vehiculo, servicios, inicio='2026-11-20T13:00:00Z'):
    return {'vehiculo': vehiculo.id, 'servicios': [s.id for s in servicios], 'inicio': inicio}


# ---------------------------------------------------------------------------
# Reserva correcta
# ---------------------------------------------------------------------------


def test_reserva_correcta_devuelve_el_turno_del_contrato(api, vehiculo, box_1, lavado, encerado):
    respuesta = api.post(URL, pedido(vehiculo, [lavado, encerado]), format='json')

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        'id': Turno.objects.get().id,
        'vehiculo': {'id': vehiculo.id, 'patente': 'AB123CD', 'tipo': 'auto'},
        'box': {'id': box_1.id, 'nombre': 'Box 1'},
        'inicio': '2026-11-20T13:00:00Z',
        'fin': '2026-11-20T14:15:00Z',
        'estado': 'pendiente',
        'precio_total': '12500.00',
        'servicios': [
            {'id': lavado.id, 'nombre': 'Lavado completo', 'precio_aplicado': '9000.00'},
            {'id': encerado.id, 'nombre': 'Encerado', 'precio_aplicado': '3500.00'},
        ],
    }


def test_el_turno_guarda_la_tarifa_de_cada_servicio(api, vehiculo, box_1, lavado, encerado):
    api.post(URL, pedido(vehiculo, [lavado, encerado]), format='json')

    guardados = {
        (i.servicio_id, i.precio, i.duracion_minutos) for i in TurnoServicio.objects.all()
    }
    assert guardados == {
        (lavado.id, Decimal('9000.00'), 45),
        (encerado.id, Decimal('3500.00'), 30),
    }


def test_el_cliente_no_puede_imponer_el_precio_el_fin_ni_el_box(
    api, vehiculo, box_1, box_2, lavado
):
    datos = pedido(vehiculo, [lavado])
    datos.update({'precio_total': '1.00', 'fin': '2026-11-20T13:05:00Z', 'box': box_2.id})

    respuesta = api.post(URL, datos, format='json')

    assert respuesta.status_code == 201
    assert respuesta.json()['precio_total'] == '9000.00'
    assert respuesta.json()['fin'] == '2026-11-20T13:45:00Z'
    assert respuesta.json()['box']['id'] == box_1.id


def test_sin_sesion_es_401(vehiculo, box_1, lavado):
    respuesta = APIClient().post(URL, pedido(vehiculo, [lavado]), format='json')

    assert respuesta.status_code == 401


def test_el_endpoint_aparece_en_la_documentacion_de_swagger(api):
    respuesta = api.get('/api/schema/')

    assert respuesta.status_code == 200
    assert '/api/turnos/' in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Validaciones (400)
# ---------------------------------------------------------------------------


def test_faltan_todos_los_campos(api, box_1):
    respuesta = api.post(URL, {}, format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        'vehiculo': ['Elegí un vehículo.'],
        'servicios': ['Elegí al menos un servicio.'],
        'inicio': ['Elegí la fecha y la hora de inicio.'],
    }


def test_sin_servicios_es_400(api, vehiculo, box_1):
    respuesta = api.post(URL, pedido(vehiculo, []), format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'servicios': ['Elegí al menos un servicio.']}


def test_un_vehiculo_de_otro_cliente_es_400(api, box_1, lavado):
    otro = Usuario.objects.create_user(username='b@test.com', email='b@test.com', password='x')
    ajeno = Vehiculo.objects.create(cliente=otro, patente='ZZ999ZZ', tipo=TipoVehiculo.AUTO)

    respuesta = api.post(URL, pedido(ajeno, [lavado]), format='json')

    assert respuesta.status_code == 400
    assert 'vehiculo' in respuesta.json()
    assert Turno.objects.count() == 0


def test_un_vehiculo_inactivo_es_400(api, vehiculo, box_1, lavado):
    vehiculo.activo = False
    vehiculo.save()

    respuesta = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert respuesta.status_code == 400
    assert 'vehiculo' in respuesta.json()


def test_un_servicio_inactivo_es_400(api, vehiculo, box_1, lavado):
    lavado.activo = False
    lavado.save()

    respuesta = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert respuesta.status_code == 400
    assert 'servicios' in respuesta.json()


def test_un_servicio_sin_tarifa_para_el_tipo_de_vehiculo_es_400(api, cliente, box_1, encerado):
    moto = Vehiculo.objects.create(cliente=cliente, patente='512ABC', tipo=TipoVehiculo.MOTO)

    respuesta = api.post(URL, pedido(moto, [encerado]), format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'servicios': ['No hay tarifa para moto en: Encerado.']}


def test_un_servicio_repetido_es_400(api, vehiculo, box_1, lavado):
    respuesta = api.post(URL, pedido(vehiculo, [lavado, lavado]), format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'servicios': ['No se puede repetir un servicio.']}


def test_una_fecha_con_formato_invalido_es_400(api, vehiculo, box_1, lavado):
    respuesta = api.post(URL, pedido(vehiculo, [lavado], inicio='mañana'), format='json')

    assert respuesta.status_code == 400
    assert 'inicio' in respuesta.json()


def test_un_inicio_en_el_pasado_es_400(api, vehiculo, box_1, lavado):
    respuesta = api.post(
        URL, pedido(vehiculo, [lavado], inicio='2026-11-10T13:00:00Z'), format='json'
    )

    assert respuesta.status_code == 400
    assert respuesta.json() == {'inicio': ['El turno tiene que ser en el futuro.']}


def test_un_turno_fuera_del_horario_de_atencion_es_400(api, vehiculo, box_1, lavado):
    # 10:00 UTC son las 7:00 en Argentina: todavía no abrieron.
    respuesta = api.post(
        URL, pedido(vehiculo, [lavado], inicio='2026-11-20T10:00:00Z'), format='json'
    )

    assert respuesta.status_code == 400
    assert 'horario de atención' in respuesta.json()['inicio'][0]


def test_un_turno_que_termina_despues_del_cierre_es_400(api, vehiculo, box_1, lavado):
    # 22:30 UTC son las 19:30 en Argentina, y el lavado dura 45 minutos: termina 20:15.
    respuesta = api.post(
        URL, pedido(vehiculo, [lavado], inicio='2026-11-20T22:30:00Z'), format='json'
    )

    assert respuesta.status_code == 400
    assert 'Terminaría a las 20:15' in respuesta.json()['inicio'][0]
    assert Turno.objects.count() == 0


# ---------------------------------------------------------------------------
# Asignación de box y superposición (409)
# ---------------------------------------------------------------------------


def test_el_segundo_turno_del_mismo_horario_va_al_siguiente_box(
    api, vehiculo, box_1, box_2, lavado
):
    primero = api.post(URL, pedido(vehiculo, [lavado]), format='json')
    segundo = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert primero.json()['box']['id'] == box_1.id
    assert segundo.status_code == 201
    assert segundo.json()['box']['id'] == box_2.id


def test_sin_ningun_box_libre_es_409(api, vehiculo, box_1, box_2, lavado):
    api.post(URL, pedido(vehiculo, [lavado]), format='json')
    api.post(URL, pedido(vehiculo, [lavado]), format='json')

    tercero = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert tercero.status_code == 409
    assert tercero.json() == {'detail': 'No hay ningún box libre en ese horario.'}
    assert Turno.objects.count() == 2


def test_sin_boxes_cargados_es_409(api, vehiculo, lavado):
    respuesta = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert respuesta.status_code == 409


def test_un_turno_consecutivo_reutiliza_el_mismo_box(api, vehiculo, box_1, lavado):
    api.post(URL, pedido(vehiculo, [lavado]), format='json')  # 13:00 a 13:45

    consecutivo = api.post(
        URL, pedido(vehiculo, [lavado], inicio='2026-11-20T13:45:00Z'), format='json'
    )

    assert consecutivo.status_code == 201
    assert consecutivo.json()['box']['id'] == box_1.id


def test_un_turno_cancelado_libera_el_box(api, vehiculo, box_1, lavado):
    primero = api.post(URL, pedido(vehiculo, [lavado]), format='json')
    Turno.objects.filter(pk=primero.json()['id']).update(estado=Estado.CANCELADO)

    nuevo = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert nuevo.status_code == 201
    assert nuevo.json()['box']['id'] == box_1.id


def test_un_box_inactivo_no_se_asigna(api, vehiculo, box_1, box_2, lavado):
    box_1.activo = False
    box_1.save()

    respuesta = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert respuesta.json()['box']['id'] == box_2.id


# ---------------------------------------------------------------------------
# Dos reservas a la vez: la base rechaza al segundo y se reintenta
# ---------------------------------------------------------------------------


def test_si_otro_cliente_gana_el_box_se_reintenta_con_el_siguiente(
    api, vehiculo, box_1, box_2, lavado, monkeypatch, crear_turno
):
    """Simula la carrera: la primera vez se elige el box 1 aunque ya lo tomaron."""
    crear_turno(box=box_1)  # el box 1 ya está ocupado a las 13:00 UTC
    elegir_real = reservas.elegir_box
    llamadas = []

    def elegir_con_carrera(box_ids, ocupados):
        llamadas.append(1)
        if len(llamadas) == 1:
            return box_1.id  # decisión vieja: el box 1 ya no estaba libre
        return elegir_real(box_ids, ocupados)

    monkeypatch.setattr(reservas, 'elegir_box', elegir_con_carrera)

    respuesta = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert respuesta.status_code == 201
    assert respuesta.json()['box']['id'] == box_2.id
    assert len(llamadas) == 2


def test_si_siempre_pierde_la_carrera_responde_409(
    api, vehiculo, box_1, lavado, monkeypatch, crear_turno
):
    crear_turno(box=box_1)
    monkeypatch.setattr(reservas, 'elegir_box', lambda box_ids, ocupados: box_1.id)

    respuesta = api.post(URL, pedido(vehiculo, [lavado]), format='json')

    assert respuesta.status_code == 409
    assert Turno.objects.count() == 1


def test_un_error_de_box_no_deja_servicios_huerfanos(api, vehiculo, lavado):
    api.post(URL, pedido(vehiculo, [lavado]), format='json')  # 409: no hay boxes

    assert TurnoServicio.objects.count() == 0
    assert Box.objects.count() == 0