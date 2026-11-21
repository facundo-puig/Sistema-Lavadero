import pytest
from rest_framework.test import APIClient

from catalogo.models import TipoVehiculo, Vehiculo

pytestmark = pytest.mark.django_db

URL = '/api/vehiculos/'


def detalle(vehiculo):
    return f'{URL}{vehiculo.id}/'


@pytest.fixture
def auto(cliente):
    return Vehiculo.objects.create(
        cliente=cliente, patente='ABC123', tipo=TipoVehiculo.AUTO
    )


@pytest.fixture
def auto_ajeno(otro_cliente):
    return Vehiculo.objects.create(
        cliente=otro_cliente, patente='ZZ999ZZ', tipo=TipoVehiculo.CAMIONETA
    )


# --- Sin sesión ---


def test_sin_sesion_es_401(auto):
    anonimo = APIClient()

    assert anonimo.get(URL).status_code == 401
    assert anonimo.post(URL, {'patente': 'XYZ789', 'tipo': 'auto'}, format='json').status_code == 401
    assert anonimo.get(detalle(auto)).status_code == 401
    assert anonimo.delete(detalle(auto)).status_code == 401


# --- Listado ---


def test_lista_solo_los_vehiculos_activos_del_cliente(
    api_cliente, cliente, auto, auto_ajeno
):
    Vehiculo.objects.create(
        cliente=cliente, patente='AB123CD', tipo=TipoVehiculo.MOTO, activo=False
    )

    respuesta = api_cliente.get(URL)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [{'id': auto.id, 'patente': 'ABC123', 'tipo': 'auto', 'activo': True}],
    }


# --- Alta ---


def test_el_alta_normaliza_la_patente_y_asigna_el_dueno(api_cliente, cliente):
    respuesta = api_cliente.post(
        URL, {'patente': 'ab 123-cd', 'tipo': 'camioneta'}, format='json'
    )

    assert respuesta.status_code == 201
    vehiculo = Vehiculo.objects.get()
    assert respuesta.json() == {
        'id': vehiculo.id,
        'patente': 'AB123CD',
        'tipo': 'camioneta',
        'activo': True,
    }
    assert vehiculo.cliente == cliente


def test_el_alta_ignora_cliente_y_activo_enviados(api_cliente, cliente, otro_cliente):
    respuesta = api_cliente.post(
        URL,
        {'patente': 'ABC123', 'tipo': 'auto', 'cliente': otro_cliente.id, 'activo': False},
        format='json',
    )

    assert respuesta.status_code == 201
    vehiculo = Vehiculo.objects.get()
    assert vehiculo.cliente == cliente
    assert vehiculo.activo is True


@pytest.mark.parametrize('patente', ['ABC123', 'AB123CD', '123ABC', 'A123BCD'])
def test_acepta_los_cuatro_formatos_de_patente(api_cliente, patente):
    respuesta = api_cliente.post(URL, {'patente': patente, 'tipo': 'auto'}, format='json')

    assert respuesta.status_code == 201
    assert respuesta.json()['patente'] == patente


@pytest.mark.parametrize('patente', ['AB12', 'ABCD1234', '12-34', 'A1B2C3', '!!!'])
def test_una_patente_con_formato_invalido_es_400(api_cliente, patente):
    respuesta = api_cliente.post(URL, {'patente': patente, 'tipo': 'auto'}, format='json')

    assert respuesta.status_code == 400
    assert 'patente' in respuesta.json()
    assert Vehiculo.objects.count() == 0


def test_la_misma_patente_escrita_distinto_es_duplicada(api_cliente, auto):
    respuesta = api_cliente.post(URL, {'patente': 'abc 123', 'tipo': 'auto'}, format='json')

    assert respuesta.status_code == 400
    assert 'patente' in respuesta.json()
    assert Vehiculo.objects.count() == 1


def test_la_patente_de_un_vehiculo_inactivo_sigue_ocupada(api_cliente, cliente):
    Vehiculo.objects.create(
        cliente=cliente, patente='XYZ789', tipo=TipoVehiculo.AUTO, activo=False
    )

    respuesta = api_cliente.post(URL, {'patente': 'XYZ789', 'tipo': 'auto'}, format='json')

    assert respuesta.status_code == 400
    assert 'patente' in respuesta.json()


def test_la_patente_de_otro_cliente_esta_ocupada(api_cliente, auto_ajeno):
    respuesta = api_cliente.post(URL, {'patente': 'zz999zz', 'tipo': 'auto'}, format='json')

    assert respuesta.status_code == 400
    assert 'patente' in respuesta.json()


def test_faltan_los_campos_es_400(api_cliente):
    respuesta = api_cliente.post(URL, {}, format='json')

    assert respuesta.status_code == 400
    assert set(respuesta.json()) == {'patente', 'tipo'}


def test_un_tipo_inexistente_es_400(api_cliente):
    respuesta = api_cliente.post(URL, {'patente': 'ABC123', 'tipo': 'avion'}, format='json')

    assert respuesta.status_code == 400
    assert 'tipo' in respuesta.json()


# --- Detalle ---


def test_detalle_de_un_vehiculo_propio(api_cliente, auto):
    respuesta = api_cliente.get(detalle(auto))

    assert respuesta.status_code == 200
    assert respuesta.json() == {'id': auto.id, 'patente': 'ABC123', 'tipo': 'auto', 'activo': True}


def test_el_detalle_de_un_vehiculo_ajeno_es_404(api_cliente, auto_ajeno):
    assert api_cliente.get(detalle(auto_ajeno)).status_code == 404


def test_el_detalle_de_un_vehiculo_inexistente_es_404(api_cliente):
    assert api_cliente.get(f'{URL}999999/').status_code == 404


# --- Edición ---


def test_put_reemplaza_patente_y_tipo(api_cliente, auto):
    respuesta = api_cliente.put(
        detalle(auto), {'patente': 'xyz-789', 'tipo': 'moto'}, format='json'
    )

    assert respuesta.status_code == 200
    auto.refresh_from_db()
    assert auto.patente == 'XYZ789'
    assert auto.tipo == 'moto'


def test_put_exige_patente_y_tipo(api_cliente, auto):
    respuesta = api_cliente.put(detalle(auto), {'patente': 'XYZ789'}, format='json')

    assert respuesta.status_code == 400
    assert 'tipo' in respuesta.json()


def test_patch_acepta_solo_el_tipo(api_cliente, auto):
    respuesta = api_cliente.patch(detalle(auto), {'tipo': 'camioneta'}, format='json')

    assert respuesta.status_code == 200
    auto.refresh_from_db()
    assert auto.tipo == 'camioneta'
    assert auto.patente == 'ABC123'


def test_patch_normaliza_la_patente(api_cliente, auto):
    respuesta = api_cliente.patch(detalle(auto), {'patente': 'ab-123 cd'}, format='json')

    assert respuesta.status_code == 200
    auto.refresh_from_db()
    assert auto.patente == 'AB123CD'


def test_editar_con_la_propia_patente_no_cuenta_como_duplicada(api_cliente, auto):
    respuesta = api_cliente.patch(detalle(auto), {'patente': 'abc123'}, format='json')

    assert respuesta.status_code == 200


def test_editar_con_la_patente_de_otro_vehiculo_es_400(api_cliente, auto, auto_ajeno):
    respuesta = api_cliente.patch(detalle(auto), {'patente': 'ZZ999ZZ'}, format='json')

    assert respuesta.status_code == 400
    assert 'patente' in respuesta.json()
    auto.refresh_from_db()
    assert auto.patente == 'ABC123'


def test_patch_no_permite_cambiar_activo(api_cliente, auto):
    respuesta = api_cliente.patch(detalle(auto), {'activo': False}, format='json')

    assert respuesta.status_code == 200
    auto.refresh_from_db()
    assert auto.activo is True


def test_editar_un_vehiculo_ajeno_es_404(api_cliente, auto_ajeno):
    respuesta = api_cliente.patch(detalle(auto_ajeno), {'tipo': 'moto'}, format='json')

    assert respuesta.status_code == 404
    auto_ajeno.refresh_from_db()
    assert auto_ajeno.tipo == 'camioneta'


# --- Baja lógica ---


def test_delete_da_de_baja_sin_borrar_la_fila(api_cliente, auto):
    respuesta = api_cliente.delete(detalle(auto))

    assert respuesta.status_code == 204
    assert respuesta.content == b''
    auto.refresh_from_db()
    assert auto.activo is False
    assert api_cliente.get(URL).json()['count'] == 0


def test_delete_de_un_vehiculo_ya_inactivo_tambien_da_204(api_cliente, auto):
    Vehiculo.objects.filter(pk=auto.pk).update(activo=False)

    assert api_cliente.delete(detalle(auto)).status_code == 204


def test_delete_de_un_vehiculo_ajeno_es_404(api_cliente, auto_ajeno):
    respuesta = api_cliente.delete(detalle(auto_ajeno))

    assert respuesta.status_code == 404
    auto_ajeno.refresh_from_db()
    assert auto_ajeno.activo is True


# --- Documentación ---


def test_los_endpoints_aparecen_en_la_documentacion_de_swagger(api_cliente):
    respuesta = api_cliente.get('/api/schema/')

    assert respuesta.status_code == 200
    assert '/api/vehiculos/' in respuesta.content.decode()
