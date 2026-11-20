import pytest

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('rol', ['administrador', 'operario'])
@pytest.mark.parametrize(
    ('metodo', 'url'),
    [
        ('get', '/api/catalogo/'),
        ('get', '/api/vehiculos/'),
        ('post', '/api/vehiculos/'),
        ('get', '/api/vehiculos/1/'),
        ('patch', '/api/vehiculos/1/'),
        ('delete', '/api/vehiculos/1/'),
    ],
)
def test_administrador_y_operario_no_acceden_al_catalogo_ni_a_vehiculos(
    request, api_de, rol, metodo, url
):
    api = api_de(request.getfixturevalue(rol))

    respuesta = getattr(api, metodo)(url)

    assert respuesta.status_code == 403


@pytest.mark.parametrize('rol', ['cliente', 'operario'])
@pytest.mark.parametrize(
    ('metodo', 'url'),
    [
        ('get', '/api/servicios/'),
        ('post', '/api/servicios/'),
        ('get', '/api/servicios/1/'),
        ('patch', '/api/servicios/1/'),
        ('delete', '/api/servicios/1/'),
        ('get', '/api/boxes/'),
        ('post', '/api/boxes/'),
        ('get', '/api/boxes/1/'),
        ('patch', '/api/boxes/1/'),
        ('delete', '/api/boxes/1/'),
    ],
)
def test_solo_el_administrador_gestiona_servicios_y_boxes(
    request, api_de, rol, metodo, url
):
    api = api_de(request.getfixturevalue(rol))

    respuesta = getattr(api, metodo)(url)

    assert respuesta.status_code == 403
