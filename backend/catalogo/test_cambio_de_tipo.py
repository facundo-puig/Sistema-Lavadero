from datetime import UTC, datetime
from decimal import Decimal

import pytest

from catalogo.models import Box, TipoVehiculo, Vehiculo
from catalogo.services import MENSAJE_CAMBIO_DE_TIPO
from turnos.estados import Estado
from turnos.models import Turno

pytestmark = pytest.mark.django_db


@pytest.fixture
def auto(cliente):
    return Vehiculo.objects.create(
        cliente=cliente, patente='ABC123', tipo=TipoVehiculo.AUTO
    )


def crear_turno(vehiculo, estado, hora=13):
    box, _ = Box.objects.get_or_create(nombre='Box 1')
    return Turno.objects.create(
        vehiculo=vehiculo,
        box=box,
        inicio=datetime(2026, 11, 20, hora, 0, tzinfo=UTC),
        fin=datetime(2026, 11, 20, hora, 45, tzinfo=UTC),
        estado=estado,
        precio_total=Decimal('9000.00'),
    )


def url(vehiculo):
    return f'/api/vehiculos/{vehiculo.id}/'


@pytest.mark.parametrize('estado', [Estado.PENDIENTE, Estado.EN_PROCESO])
def test_no_se_cambia_el_tipo_con_turnos_pendientes_o_en_proceso(
    api_cliente, auto, estado
):
    crear_turno(auto, estado)

    respuesta = api_cliente.patch(url(auto), {'tipo': 'camioneta'}, format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'tipo': [MENSAJE_CAMBIO_DE_TIPO]}
    auto.refresh_from_db()
    assert auto.tipo == 'auto'


def test_put_tampoco_cambia_el_tipo_con_turnos_en_curso(api_cliente, auto):
    crear_turno(auto, Estado.PENDIENTE)

    respuesta = api_cliente.put(
        url(auto), {'patente': 'ABC123', 'tipo': 'moto'}, format='json'
    )

    assert respuesta.status_code == 400
    assert 'tipo' in respuesta.json()


@pytest.mark.parametrize(
    'estado', [Estado.FINALIZADO, Estado.ENTREGADO, Estado.CANCELADO]
)
def test_se_cambia_el_tipo_si_los_turnos_ya_terminaron(api_cliente, auto, estado):
    crear_turno(auto, estado)

    respuesta = api_cliente.patch(url(auto), {'tipo': 'camioneta'}, format='json')

    assert respuesta.status_code == 200
    auto.refresh_from_db()
    assert auto.tipo == 'camioneta'


def test_enviar_el_mismo_tipo_no_cuenta_como_cambio(api_cliente, auto):
    crear_turno(auto, Estado.PENDIENTE)

    respuesta = api_cliente.patch(url(auto), {'tipo': 'auto'}, format='json')

    assert respuesta.status_code == 200


def test_se_puede_editar_la_patente_con_turnos_en_curso(api_cliente, auto):
    crear_turno(auto, Estado.PENDIENTE)

    respuesta = api_cliente.patch(url(auto), {'patente': 'ab 123 cd'}, format='json')

    assert respuesta.status_code == 200
    auto.refresh_from_db()
    assert auto.patente == 'AB123CD'


def test_los_turnos_de_otro_vehiculo_no_bloquean_el_cambio(api_cliente, cliente, auto):
    otro = Vehiculo.objects.create(
        cliente=cliente, patente='XYZ789', tipo=TipoVehiculo.AUTO
    )
    crear_turno(otro, Estado.PENDIENTE)

    respuesta = api_cliente.patch(url(auto), {'tipo': 'moto'}, format='json')

    assert respuesta.status_code == 200
