from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from catalogo.models import Box, Servicio, Tarifa, Vehiculo

pytestmark = pytest.mark.django_db

Usuario = get_user_model()
CONTRASENA = 'Lavadero123!'


def cargar(**opciones):
    call_command('cargar_datos', stdout=StringIO(), **opciones)


@pytest.fixture(autouse=True)
def modo_desarrollo(settings):
    settings.DEBUG = True


def test_crea_dos_boxes_activos():
    cargar()

    boxes = Box.objects.order_by('id').values_list('nombre', 'activo')
    assert list(boxes) == [('Box 1', True), ('Box 2', True)]


def test_crea_los_servicios_con_su_tarifa_por_tipo_de_vehiculo():
    cargar()

    assert Servicio.objects.count() == 4
    assert Tarifa.objects.count() == 11
    aspirado = Servicio.objects.get(nombre='Aspirado interior')
    tipos = set(aspirado.tarifas.values_list('tipo_vehiculo', flat=True))
    assert tipos == {'auto', 'camioneta'}


@pytest.mark.parametrize(
    ('email', 'rol'),
    [
        ('admin@lavadero.test', 'ADMINISTRADOR'),
        ('operario@lavadero.test', 'OPERARIO'),
        ('cliente@lavadero.test', 'CLIENTE'),
    ],
)
def test_crea_el_administrador_el_operario_y_el_cliente(email, rol):
    cargar()

    usuario = Usuario.objects.get(email=email)
    assert usuario.rol == rol
    assert usuario.username == email
    assert usuario.check_password(CONTRASENA)


def test_el_cliente_tiene_un_vehiculo():
    cargar()

    assert Vehiculo.objects.get().cliente.email == 'cliente@lavadero.test'


def test_correrlo_dos_veces_no_duplica_nada():
    cargar()
    cargar()

    assert Box.objects.count() == 2
    assert Servicio.objects.count() == 4
    assert Tarifa.objects.count() == 11
    assert Usuario.objects.count() == 3
    assert Vehiculo.objects.count() == 1


def test_no_pisa_la_contrasena_de_un_usuario_existente():
    cargar()
    usuario = Usuario.objects.get(email='operario@lavadero.test')
    usuario.set_password('otra-clave-123')
    usuario.save()

    cargar()

    usuario.refresh_from_db()
    assert usuario.check_password('otra-clave-123')


def test_con_debug_apagado_exige_forzar(settings):
    settings.DEBUG = False

    with pytest.raises(CommandError):
        cargar()
    assert Usuario.objects.count() == 0

    cargar(forzar=True)
    assert Usuario.objects.count() == 3


def test_el_operario_de_ejemplo_puede_iniciar_sesion():
    cargar()

    respuesta = APIClient().post(
        '/api/auth/login/',
        {'email': 'operario@lavadero.test', 'password': CONTRASENA},
        format='json',
    )

    assert respuesta.status_code == 200
    assert respuesta.data['usuario']['rol'] == 'OPERARIO'


def test_el_cliente_ve_el_catalogo_cargado():
    cargar()
    api = APIClient()
    api.force_authenticate(Usuario.objects.get(email='cliente@lavadero.test'))

    respuesta = api.get('/api/catalogo/')

    assert respuesta.status_code == 200
    assert len(respuesta.data) == 4
