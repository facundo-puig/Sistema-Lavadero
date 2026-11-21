
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

Usuario = get_user_model()
URL_USUARIOS = '/api/auth/usuarios/'


@pytest.fixture
def administrador(db):
    return Usuario.objects.create_user(
        username='admin@test.com',
        email='admin@test.com',
        password='ClaveSegura123!',
        rol=Usuario.Rol.ADMINISTRADOR,
    )


@pytest.fixture
def cliente(db):
    return Usuario.objects.create_user(
        username='cliente@test.com',
        email='cliente@test.com',
        password='ClaveSegura123!',
        rol=Usuario.Rol.CLIENTE,
    )


@pytest.fixture
def operario(db):
    return Usuario.objects.create_user(
        username='operario@test.com',
        email='operario@test.com',
        password='ClaveSegura123!',
        rol=Usuario.Rol.OPERARIO,
    )


@pytest.fixture
def api_administrador(administrador):
    api = APIClient()
    api.force_authenticate(user=administrador)
    return api


@pytest.mark.django_db
def test_solo_administrador_puede_listar(api_administrador, cliente, operario):
    respuesta = api_administrador.get(URL_USUARIOS)

    assert respuesta.status_code == 200
    assert 'results' in respuesta.data
    assert 'count' in respuesta.data

    for usuario in (cliente, operario):
        api = APIClient()
        api.force_authenticate(user=usuario)

        respuesta = api.get(URL_USUARIOS)
        assert respuesta.status_code == 403

    respuesta = APIClient().get(URL_USUARIOS)
    assert respuesta.status_code == 401


@pytest.mark.django_db
def test_filtrar_usuarios_por_rol(api_administrador, cliente, operario):
    respuesta = api_administrador.get(
        URL_USUARIOS,
        {'rol': 'CLIENTE'},
    )

    assert respuesta.status_code == 200
    assert respuesta.data['count'] == 1
    assert respuesta.data['results'][0]['id'] == cliente.id
    assert respuesta.data['results'][0]['rol'] == 'CLIENTE'

    respuesta = api_administrador.get(
        URL_USUARIOS,
        {'rol': 'INVALIDO'},
    )

    assert respuesta.status_code == 400
    assert 'rol' in respuesta.data


@pytest.mark.django_db
def test_listado_paginado(api_administrador):
    for numero in range(12):
        Usuario.objects.create_user(
            username=f'cliente{numero}',
            email=f'cliente{numero}@test.com',
            password='ClaveSegura123!',
        )

    respuesta = api_administrador.get(URL_USUARIOS)

    assert respuesta.status_code == 200
    assert respuesta.data['count'] == 13
    assert len(respuesta.data['results']) == 10
    assert respuesta.data['next'] is not None


@pytest.mark.django_db
@pytest.mark.parametrize('rol', ['OPERARIO', 'ADMINISTRADOR'])
def test_administrador_puede_crear_empleados(api_administrador, rol):
    datos = {
        'nombre': 'Nuevo empleado',
        'email': 'nuevo@test.com',
        'password': 'ClaveSegura123!',
        'rol': rol,
    }

    respuesta = api_administrador.post(
        URL_USUARIOS,
        datos,
        format='json',
    )

    assert respuesta.status_code == 201
    assert respuesta.data['rol'] == rol
    assert 'password' not in respuesta.data

    usuario = Usuario.objects.get(email='nuevo@test.com')
    assert usuario.check_password(datos['password'])


@pytest.mark.django_db
def test_no_se_puede_crear_cliente_desde_administracion(api_administrador):
    respuesta = api_administrador.post(
        URL_USUARIOS,
        {
            'nombre': 'Nuevo cliente',
            'email': 'nuevo@test.com',
            'password': 'ClaveSegura123!',
            'rol': 'CLIENTE',
        },
        format='json',
    )

    assert respuesta.status_code == 400
    assert 'rol' in respuesta.data


@pytest.mark.django_db
def test_administrador_puede_cambiar_rol(api_administrador, cliente):
    respuesta = api_administrador.patch(
        f'{URL_USUARIOS}{cliente.id}/rol/',
        {'rol': 'OPERARIO'},
        format='json',
    )

    assert respuesta.status_code == 200

    cliente.refresh_from_db()
    assert cliente.rol == Usuario.Rol.OPERARIO


@pytest.mark.django_db
def test_administrador_no_puede_quitarse_su_rol(
    api_administrador,
    administrador,
):
    respuesta = api_administrador.patch(
        f'{URL_USUARIOS}{administrador.id}/rol/',
        {'rol': 'CLIENTE'},
        format='json',
    )

    assert respuesta.status_code == 400

    administrador.refresh_from_db()
    assert administrador.rol == Usuario.Rol.ADMINISTRADOR


@pytest.mark.django_db
def test_baja_logica_de_usuario(api_administrador, cliente):
    respuesta = api_administrador.delete(
        f'{URL_USUARIOS}{cliente.id}/'
    )

    assert respuesta.status_code == 204

    cliente.refresh_from_db()
    assert cliente.is_active is False
    assert Usuario.objects.filter(pk=cliente.id).exists()

    respuesta_login = APIClient().post(
        '/api/auth/login/',
        {
            'email': cliente.email,
            'password': 'ClaveSegura123!',
        },
        format='json',
    )

    assert respuesta_login.status_code == 401


@pytest.mark.django_db
def test_administrador_no_puede_darse_de_baja(
    api_administrador,
    administrador,
):
    respuesta = api_administrador.delete(
        f'{URL_USUARIOS}{administrador.id}/'
    )

    assert respuesta.status_code == 400

    administrador.refresh_from_db()
    assert administrador.is_active is True
