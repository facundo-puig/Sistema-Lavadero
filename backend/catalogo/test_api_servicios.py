from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from catalogo.models import Servicio, Tarifa, TipoVehiculo

pytestmark = pytest.mark.django_db

URL = '/api/servicios/'


def detalle(servicio):
    return f'{URL}{servicio.id}/'


def tarifa(tipo, precio, minutos):
    return {'tipo_vehiculo': tipo, 'precio': precio, 'duracion_minutos': minutos}


@pytest.fixture
def lavado(db):
    servicio = Servicio.objects.create(
        nombre='Lavado completo', descripcion='Exterior, interior y aspirado.'
    )
    Tarifa.objects.create(
        servicio=servicio,
        tipo_vehiculo=TipoVehiculo.AUTO,
        precio=Decimal('12500.00'),
        duracion_minutos=45,
    )
    Tarifa.objects.create(
        servicio=servicio,
        tipo_vehiculo=TipoVehiculo.CAMIONETA,
        precio=Decimal('16000.00'),
        duracion_minutos=60,
    )
    return servicio


# --- Sin sesión ---


def test_sin_sesion_es_401(lavado):
    anonimo = APIClient()

    assert anonimo.get(URL).status_code == 401
    assert anonimo.post(URL, {'nombre': 'X'}, format='json').status_code == 401
    assert anonimo.delete(detalle(lavado)).status_code == 401


# --- Listado y detalle ---


def test_el_listado_incluye_las_tarifas_y_va_paginado(api_admin, lavado):
    auto, camioneta = lavado.tarifas.order_by('id')

    respuesta = api_admin.get(URL)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [
            {
                'id': lavado.id,
                'nombre': 'Lavado completo',
                'descripcion': 'Exterior, interior y aspirado.',
                'activo': True,
                'tarifas': [
                    {
                        'id': auto.id,
                        'tipo_vehiculo': 'auto',
                        'precio': '12500.00',
                        'duracion_minutos': 45,
                    },
                    {
                        'id': camioneta.id,
                        'tipo_vehiculo': 'camioneta',
                        'precio': '16000.00',
                        'duracion_minutos': 60,
                    },
                ],
            }
        ],
    }


def test_filtra_por_activo(api_admin, lavado):
    inactivo = Servicio.objects.create(nombre='Pulido', activo=False)

    activos = api_admin.get(URL, {'activo': 'true'}).json()['results']
    inactivos = api_admin.get(URL, {'activo': 'false'}).json()['results']

    assert [s['id'] for s in activos] == [lavado.id]
    assert [s['id'] for s in inactivos] == [inactivo.id]


def test_detalle_de_un_servicio(api_admin, lavado):
    respuesta = api_admin.get(detalle(lavado))

    assert respuesta.status_code == 200
    assert respuesta.json()['nombre'] == 'Lavado completo'
    assert len(respuesta.json()['tarifas']) == 2


def test_un_servicio_inexistente_da_404(api_admin):
    assert api_admin.get(f'{URL}999999/').status_code == 404
    assert api_admin.patch(f'{URL}999999/', {'activo': False}, format='json').status_code == 404
    assert api_admin.delete(f'{URL}999999/').status_code == 404


# --- Alta ---


def test_el_alta_crea_el_servicio_con_sus_tarifas(api_admin):
    respuesta = api_admin.post(
        URL,
        {
            'nombre': 'Encerado',
            'descripcion': 'Cera protectora.',
            'tarifas': [tarifa('auto', '9000.00', 40), tarifa('moto', '5000.00', 30)],
        },
        format='json',
    )

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos['nombre'] == 'Encerado'
    assert datos['descripcion'] == 'Cera protectora.'
    assert datos['activo'] is True
    assert [(t['tipo_vehiculo'], t['precio'], t['duracion_minutos']) for t in datos['tarifas']] == [
        ('auto', '9000.00', 40),
        ('moto', '5000.00', 30),
    ]
    assert Servicio.objects.count() == 1
    assert Tarifa.objects.count() == 2


def test_el_alta_ignora_el_activo_enviado(api_admin):
    respuesta = api_admin.post(
        URL, {'nombre': 'Encerado', 'activo': False}, format='json'
    )

    assert respuesta.status_code == 201
    assert Servicio.objects.get().activo is True


def test_el_alta_sin_tarifas_es_valida(api_admin):
    respuesta = api_admin.post(URL, {'nombre': 'Encerado'}, format='json')

    assert respuesta.status_code == 201
    assert respuesta.json()['tarifas'] == []


@pytest.mark.parametrize('cuerpo', [{}, {'nombre': ''}, {'nombre': '   '}])
def test_el_alta_sin_nombre_es_400(api_admin, cuerpo):
    respuesta = api_admin.post(URL, cuerpo, format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'nombre': ['Ingresá el nombre del servicio.']}
    assert Servicio.objects.count() == 0


@pytest.mark.parametrize('precio', ['0', '0.00', '-5', 'abc', '12.345'])
def test_un_precio_invalido_es_400(api_admin, precio):
    respuesta = api_admin.post(
        URL,
        {'nombre': 'Encerado', 'tarifas': [tarifa('auto', precio, 40)]},
        format='json',
    )

    assert respuesta.status_code == 400
    assert 'precio' in respuesta.json()['tarifas'][0]
    assert Servicio.objects.count() == 0


@pytest.mark.parametrize('duracion', [0, -10, 'abc'])
def test_una_duracion_invalida_es_400(api_admin, duracion):
    respuesta = api_admin.post(
        URL,
        {'nombre': 'Encerado', 'tarifas': [tarifa('auto', '9000.00', duracion)]},
        format='json',
    )

    assert respuesta.status_code == 400
    assert 'duracion_minutos' in respuesta.json()['tarifas'][0]
    assert Servicio.objects.count() == 0


def test_un_tipo_de_vehiculo_inexistente_es_400(api_admin):
    respuesta = api_admin.post(
        URL,
        {'nombre': 'Encerado', 'tarifas': [tarifa('avion', '9000.00', 40)]},
        format='json',
    )

    assert respuesta.status_code == 400
    assert 'tipo_vehiculo' in respuesta.json()['tarifas'][0]


def test_un_tipo_de_vehiculo_repetido_es_400(api_admin):
    respuesta = api_admin.post(
        URL,
        {
            'nombre': 'Encerado',
            'tarifas': [tarifa('auto', '9000.00', 40), tarifa('auto', '9500.00', 45)],
        },
        format='json',
    )

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        'tarifas': ['No se puede repetir el tipo de vehículo en las tarifas.']
    }
    assert Servicio.objects.count() == 0


def test_una_tarifa_sin_precio_es_400(api_admin):
    respuesta = api_admin.post(
        URL,
        {'nombre': 'Encerado', 'tarifas': [{'tipo_vehiculo': 'auto', 'duracion_minutos': 40}]},
        format='json',
    )

    assert respuesta.status_code == 400
    assert respuesta.json()['tarifas'][0] == {'precio': ['Ingresá el precio.']}


# --- Edición ---


def test_put_exige_el_nombre(api_admin, lavado):
    respuesta = api_admin.put(detalle(lavado), {'descripcion': 'Otra'}, format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'nombre': ['Ingresá el nombre del servicio.']}


def test_put_edita_los_datos_y_no_toca_las_tarifas_si_no_se_envian(api_admin, lavado):
    respuesta = api_admin.put(
        detalle(lavado),
        {'nombre': 'Lavado premium', 'descripcion': 'Nueva.'},
        format='json',
    )

    assert respuesta.status_code == 200
    lavado.refresh_from_db()
    assert lavado.nombre == 'Lavado premium'
    assert lavado.descripcion == 'Nueva.'
    assert lavado.tarifas.count() == 2
    assert len(respuesta.json()['tarifas']) == 2


def test_patch_sin_tarifas_no_las_cambia(api_admin, lavado):
    respuesta = api_admin.patch(detalle(lavado), {'nombre': 'Otro'}, format='json')

    assert respuesta.status_code == 200
    assert lavado.tarifas.get(tipo_vehiculo='auto').precio == Decimal('12500.00')
    assert lavado.tarifas.count() == 2


def test_patch_da_de_baja_y_reactiva(api_admin, lavado):
    baja = api_admin.patch(detalle(lavado), {'activo': False}, format='json')
    alta = api_admin.patch(detalle(lavado), {'activo': True}, format='json')

    assert baja.json()['activo'] is False
    assert alta.json()['activo'] is True


def test_patch_crea_o_actualiza_las_tarifas_segun_el_tipo(api_admin, lavado):
    respuesta = api_admin.patch(
        detalle(lavado),
        {'tarifas': [tarifa('auto', '13000.00', 50), tarifa('moto', '6000.00', 25)]},
        format='json',
    )

    assert respuesta.status_code == 200
    por_tipo = {t.tipo_vehiculo: t for t in lavado.tarifas.all()}
    assert set(por_tipo) == {'auto', 'camioneta', 'moto'}
    assert por_tipo['auto'].precio == Decimal('13000.00')
    assert por_tipo['auto'].duracion_minutos == 50
    assert por_tipo['camioneta'].precio == Decimal('16000.00')  # no se envió: queda igual
    assert por_tipo['moto'].precio == Decimal('6000.00')
    assert [t['tipo_vehiculo'] for t in respuesta.json()['tarifas']] == [
        'auto',
        'camioneta',
        'moto',
    ]


def test_patch_con_una_tarifa_incompleta_es_400(api_admin, lavado):
    respuesta = api_admin.patch(
        detalle(lavado), {'tarifas': [{'tipo_vehiculo': 'auto'}]}, format='json'
    )

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        'tarifas': [
            {
                'precio': ['Ingresá el precio.'],
                'duracion_minutos': ['Ingresá la duración en minutos.'],
            }
        ]
    }


def test_patch_con_una_tarifa_invalida_no_cambia_nada(api_admin, lavado):
    respuesta = api_admin.patch(
        detalle(lavado),
        {'tarifas': [tarifa('auto', '99999.00', 50), tarifa('moto', '0', 25)]},
        format='json',
    )

    assert respuesta.status_code == 400
    assert lavado.tarifas.get(tipo_vehiculo='auto').precio == Decimal('12500.00')
    assert not lavado.tarifas.filter(tipo_vehiculo='moto').exists()


def test_patch_con_un_tipo_repetido_es_400(api_admin, lavado):
    respuesta = api_admin.patch(
        detalle(lavado),
        {'tarifas': [tarifa('moto', '6000.00', 25), tarifa('moto', '6500.00', 30)]},
        format='json',
    )

    assert respuesta.status_code == 400
    assert 'tarifas' in respuesta.json()


# --- Baja lógica ---


def test_delete_da_de_baja_sin_borrar_el_servicio_ni_sus_tarifas(api_admin, lavado):
    respuesta = api_admin.delete(detalle(lavado))

    assert respuesta.status_code == 204
    assert respuesta.content == b''
    lavado.refresh_from_db()
    assert lavado.activo is False
    assert lavado.tarifas.count() == 2


def test_delete_de_un_servicio_ya_inactivo_tambien_da_204(api_admin, lavado):
    Servicio.objects.filter(pk=lavado.pk).update(activo=False)

    assert api_admin.delete(detalle(lavado)).status_code == 204


# --- Relación con el catálogo para reservar ---


def test_un_servicio_dado_de_baja_sale_del_catalogo(api_admin, api_cliente, lavado):
    assert [s['id'] for s in api_cliente.get('/api/catalogo/').json()] == [lavado.id]

    api_admin.delete(detalle(lavado))

    assert api_cliente.get('/api/catalogo/').json() == []


def test_un_servicio_nuevo_aparece_en_el_catalogo(api_admin, api_cliente):
    api_admin.post(
        URL,
        {'nombre': 'Encerado', 'tarifas': [tarifa('auto', '9000.00', 40)]},
        format='json',
    )

    nombres = [s['nombre'] for s in api_cliente.get('/api/catalogo/').json()]

    assert nombres == ['Encerado']


# --- Documentación ---


def test_los_endpoints_aparecen_en_la_documentacion_de_swagger(api_admin):
    respuesta = api_admin.get('/api/schema/')

    assert respuesta.status_code == 200
    assert '/api/servicios/' in respuesta.content.decode()


def test_los_errores_de_tarifas_son_una_lista_con_un_elemento_por_tarifa(api_admin):
    respuesta = api_admin.post(
        URL,
        {
            'nombre': 'Encerado',
            'tarifas': [tarifa('auto', '9000.00', 40), tarifa('moto', '0', 30)],
        },
        format='json',
    )

    assert respuesta.status_code == 400
    errores = respuesta.json()['tarifas']
    assert isinstance(errores, list)
    assert errores[0] == {}
    assert 'precio' in errores[1]