
import pytest
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from usuarios.permisos import (
    EsAdministrador,
    EsAdministradorOOperario,
    EsCliente,
    EsOperario,
)


@pytest.fixture
def usuarios_por_rol(db):
    Usuario = get_user_model()
    usuarios = {}

    for rol in (
        Usuario.Rol.ADMINISTRADOR,
        Usuario.Rol.OPERARIO,
        Usuario.Rol.CLIENTE,
    ):
        email = f'{rol.lower()}@ejemplo.com'

        usuarios[rol] = Usuario.objects.create_user(
            username=email,
            email=email,
            password='Prueba12345!',
            rol=rol,
        )

    return usuarios


def crear_vista(permiso):
    class VistaPrueba(APIView):
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated, permiso]

        def get(self, request):
            return Response({'detail': 'Acceso permitido'})

    return VistaPrueba.as_view()


@pytest.mark.parametrize(
    ('permiso', 'rol', 'codigo_esperado'),
    [
        (EsAdministrador, 'ADMINISTRADOR', 200),
        (EsAdministrador, 'OPERARIO', 403),
        (EsAdministrador, 'CLIENTE', 403),
        (EsOperario, 'ADMINISTRADOR', 403),
        (EsOperario, 'OPERARIO', 200),
        (EsOperario, 'CLIENTE', 403),
        (EsCliente, 'ADMINISTRADOR', 403),
        (EsCliente, 'OPERARIO', 403),
        (EsCliente, 'CLIENTE', 200),
        (EsAdministradorOOperario, 'ADMINISTRADOR', 200),
        (EsAdministradorOOperario, 'OPERARIO', 200),
        (EsAdministradorOOperario, 'CLIENTE', 403),
    ],
)
def test_permiso_segun_rol(
    usuarios_por_rol,
    permiso,
    rol,
    codigo_esperado,
):
    request = APIRequestFactory().get('/api/prueba/')
    force_authenticate(request, user=usuarios_por_rol[rol])

    respuesta = crear_vista(permiso)(request)

    assert respuesta.status_code == codigo_esperado


@pytest.mark.parametrize(
    'permiso',
    [
        EsAdministrador,
        EsOperario,
        EsCliente,
        EsAdministradorOOperario,
    ],
)
def test_permiso_sin_autenticacion_devuelve_401(permiso):
    request = APIRequestFactory().get('/api/prueba/')

    respuesta = crear_vista(permiso)(request)

    assert respuesta.status_code == 401
