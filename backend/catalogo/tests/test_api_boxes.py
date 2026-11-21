import pytest
from rest_framework.test import APIClient

from catalogo.models import Box

pytestmark = pytest.mark.django_db

URL = '/api/boxes/'


def detalle(box):
    return f'{URL}{box.id}/'


@pytest.fixture
def box_1(db):
    return Box.objects.create(nombre='Box 1')


# --- Sin sesión ---


def test_sin_sesion_es_401(box_1):
    anonimo = APIClient()

    assert anonimo.get(URL).status_code == 401
    assert anonimo.post(URL, {'nombre': 'Box 2'}, format='json').status_code == 401
    assert anonimo.delete(detalle(box_1)).status_code == 401


# --- Listado y detalle ---


def test_el_listado_va_paginado_y_ordenado_por_id(api_admin, box_1):
    box_2 = Box.objects.create(nombre='Box 2')

    respuesta = api_admin.get(URL)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        'count': 2,
        'next': None,
        'previous': None,
        'results': [
            {'id': box_1.id, 'nombre': 'Box 1', 'activo': True},
            {'id': box_2.id, 'nombre': 'Box 2', 'activo': True},
        ],
    }


def test_filtra_por_activo(api_admin, box_1):
    inactivo = Box.objects.create(nombre='Box 2', activo=False)

    activos = api_admin.get(URL, {'activo': 'true'}).json()['results']
    inactivos = api_admin.get(URL, {'activo': 'false'}).json()['results']

    assert [b['id'] for b in activos] == [box_1.id]
    assert [b['id'] for b in inactivos] == [inactivo.id]


def test_detalle_de_un_box(api_admin, box_1):
    respuesta = api_admin.get(detalle(box_1))

    assert respuesta.status_code == 200
    assert respuesta.json() == {'id': box_1.id, 'nombre': 'Box 1', 'activo': True}


def test_un_box_inexistente_da_404(api_admin):
    assert api_admin.get(f'{URL}999999/').status_code == 404
    assert api_admin.patch(f'{URL}999999/', {'activo': False}, format='json').status_code == 404
    assert api_admin.delete(f'{URL}999999/').status_code == 404


# --- Alta ---


def test_el_alta_crea_un_box_activo_y_recorta_el_nombre(api_admin):
    respuesta = api_admin.post(URL, {'nombre': '  Box 3  '}, format='json')

    assert respuesta.status_code == 201
    box = Box.objects.get()
    assert respuesta.json() == {'id': box.id, 'nombre': 'Box 3', 'activo': True}


def test_el_alta_ignora_el_activo_enviado(api_admin):
    respuesta = api_admin.post(URL, {'nombre': 'Box 3', 'activo': False}, format='json')

    assert respuesta.status_code == 201
    assert Box.objects.get().activo is True


@pytest.mark.parametrize('cuerpo', [{}, {'nombre': ''}, {'nombre': '   '}])
def test_el_alta_sin_nombre_es_400(api_admin, cuerpo):
    respuesta = api_admin.post(URL, cuerpo, format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'nombre': ['Ingresá el nombre del box.']}
    assert Box.objects.count() == 0


def test_un_nombre_repetido_es_400(api_admin, box_1):
    respuesta = api_admin.post(URL, {'nombre': 'Box 1'}, format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'nombre': ['Ya existe un box con ese nombre.']}
    assert Box.objects.count() == 1


def test_un_nombre_demasiado_largo_es_400(api_admin):
    respuesta = api_admin.post(URL, {'nombre': 'B' * 51}, format='json')

    assert respuesta.status_code == 400
    assert 'nombre' in respuesta.json()


# --- Edición ---


def test_put_exige_el_nombre(api_admin, box_1):
    respuesta = api_admin.put(detalle(box_1), {'activo': False}, format='json')

    assert respuesta.status_code == 400
    assert respuesta.json() == {'nombre': ['Ingresá el nombre del box.']}


def test_put_cambia_el_nombre(api_admin, box_1):
    respuesta = api_admin.put(detalle(box_1), {'nombre': 'Box principal'}, format='json')

    assert respuesta.status_code == 200
    box_1.refresh_from_db()
    assert box_1.nombre == 'Box principal'


def test_patch_da_de_baja_y_reactiva(api_admin, box_1):
    baja = api_admin.patch(detalle(box_1), {'activo': False}, format='json')
    alta = api_admin.patch(detalle(box_1), {'activo': True}, format='json')

    assert baja.json()['activo'] is False
    assert alta.json()['activo'] is True


def test_editar_con_el_propio_nombre_no_cuenta_como_repetido(api_admin, box_1):
    respuesta = api_admin.patch(detalle(box_1), {'nombre': 'Box 1'}, format='json')

    assert respuesta.status_code == 200


def test_renombrar_con_el_nombre_de_otro_box_es_400(api_admin, box_1):
    Box.objects.create(nombre='Box 2')

    respuesta = api_admin.patch(detalle(box_1), {'nombre': 'Box 2'}, format='json')

    assert respuesta.status_code == 400
    assert 'nombre' in respuesta.json()
    box_1.refresh_from_db()
    assert box_1.nombre == 'Box 1'


# --- Baja lógica ---


def test_delete_da_de_baja_sin_borrar_la_fila(api_admin, box_1):
    respuesta = api_admin.delete(detalle(box_1))

    assert respuesta.status_code == 204
    assert respuesta.content == b''
    box_1.refresh_from_db()
    assert box_1.activo is False


def test_delete_de_un_box_ya_inactivo_tambien_da_204(api_admin, box_1):
    Box.objects.filter(pk=box_1.pk).update(activo=False)

    assert api_admin.delete(detalle(box_1)).status_code == 204


# --- Documentación ---


def test_los_endpoints_aparecen_en_la_documentacion_de_swagger(api_admin):
    respuesta = api_admin.get('/api/schema/')

    assert respuesta.status_code == 200
    assert '/api/boxes/' in respuesta.content.decode()
