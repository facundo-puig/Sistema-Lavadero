from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from catalogo.models import Servicio, Tarifa, TipoVehiculo

pytestmark = pytest.mark.django_db

URL = '/api/catalogo/'


def test_sin_sesion_devuelve_401():
    assert APIClient().get(URL).status_code == 401


def test_devuelve_solo_servicios_activos_ordenados_por_nombre(api_cliente):
    Servicio.objects.create(nombre='Encerado')
    Servicio.objects.create(nombre='Abrillantado')
    Servicio.objects.create(nombre='Inactivo', activo=False)

    respuesta = api_cliente.get(URL)

    assert respuesta.status_code == 200
    assert isinstance(respuesta.data, list)  # lista completa, sin paginar
    assert [s['nombre'] for s in respuesta.data] == ['Abrillantado', 'Encerado']


def test_incluye_las_tarifas_con_importe_como_texto(api_cliente):
    servicio = Servicio.objects.create(nombre='Lavado completo')
    tarifa = Tarifa.objects.create(
        servicio=servicio,
        tipo_vehiculo=TipoVehiculo.AUTO,
        precio=Decimal('12500.00'),
        duracion_minutos=45,
    )

    respuesta = api_cliente.get(URL)

    assert respuesta.data[0]['tarifas'] == [
        {
            'id': tarifa.id,
            'tipo_vehiculo': 'auto',
            'precio': '12500.00',
            'duracion_minutos': 45,
        }
    ]


def test_servicio_sin_tarifas_devuelve_lista_vacia(api_cliente):
    Servicio.objects.create(nombre='Sin tarifas')

    respuesta = api_cliente.get(URL)

    assert respuesta.data[0]['tarifas'] == []
