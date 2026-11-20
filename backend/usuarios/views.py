
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .permisos import EsAdministrador
from .serializers import (
    CambiarRolSerializer,
    CrearUsuarioAdministracionSerializer,
    LoginRespuestaSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegistroRespuestaSerializer,
    RegistroSerializer,
    UsuarioAdministracionSerializer,
)
from .services import cerrar_sesion, iniciar_sesion, registrar_cliente


class LoginView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginRespuestaSerializer},
        description='Iniciar sesión con email y contraseña.',
        tags=['Autenticación'],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resultado = iniciar_sesion(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )

        return Response(resultado, status=status.HTTP_200_OK)


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={204: None},
        description='Cierra la sesión invalidando el refresh token.',
        tags=['Autenticación'],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cerrar_sesion(
            usuario=request.user,
            refresh_token=serializer.validated_data['refresh'],
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class RegistroView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegistroSerializer,
        responses={201: RegistroRespuestaSerializer},
        description='Registrar un nuevo usuario con rol CLIENTE.',
        tags=['Autenticación'],
    )
    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resultado = registrar_cliente(
            nombre=serializer.validated_data['nombre'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )

        return Response(resultado, status=status.HTTP_201_CREATED)



class PaginacionUsuarios(PageNumberPagination):
    page_size = 10


class AdministracionUsuariosView(APIView):
    permission_classes = [EsAdministrador]

    @extend_schema(
        responses={200: UsuarioAdministracionSerializer(many=True)},
        description='Lista usuarios con paginación y filtro por rol.',
        tags=['Administración de usuarios'],
    )
    def get(self, request):
        Usuario = get_user_model()
        usuarios = Usuario.objects.all().order_by('id')

        rol = request.query_params.get('rol')

        if rol:
            roles_validos = Usuario.Rol.values

            if rol not in roles_validos:
                raise ValidationError({
                    'rol': 'El rol indicado no es válido.'
                })

            usuarios = usuarios.filter(rol=rol)

        paginador = PaginacionUsuarios()
        pagina = paginador.paginate_queryset(usuarios, request)

        serializer = UsuarioAdministracionSerializer(
            pagina,
            many=True,
        )

        return paginador.get_paginated_response(serializer.data)

    @extend_schema(
        request=CrearUsuarioAdministracionSerializer,
        responses={201: UsuarioAdministracionSerializer},
        description='Crea un operario o administrador.',
        tags=['Administración de usuarios'],
    )
    def post(self, request):
        serializer = CrearUsuarioAdministracionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data
        Usuario = get_user_model()

        usuario = Usuario.objects.create_user(
            username=datos['email'],
            email=datos['email'],
            password=datos['password'],
            first_name=datos['nombre'].strip(),
            rol=datos['rol'],
        )

        respuesta = UsuarioAdministracionSerializer(usuario)

        return Response(
            respuesta.data,
            status=status.HTTP_201_CREATED,
        )


class CambiarRolUsuarioView(APIView):
    permission_classes = [EsAdministrador]

    @extend_schema(
        request=CambiarRolSerializer,
        responses={200: UsuarioAdministracionSerializer},
        description='Cambia el rol de un usuario.',
        tags=['Administración de usuarios'],
    )
    def patch(self, request, usuario_id):
        Usuario = get_user_model()
        usuario = get_object_or_404(Usuario, pk=usuario_id)

        serializer = CambiarRolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nuevo_rol = serializer.validated_data['rol']

        if usuario.pk == request.user.pk and nuevo_rol != 'ADMINISTRADOR':
            raise ValidationError({
                'rol': 'No podés quitarte tu propio rol de administrador.'
            })

        usuario.rol = nuevo_rol
        usuario.save(update_fields=['rol'])

        return Response(
            UsuarioAdministracionSerializer(usuario).data,
            status=status.HTTP_200_OK,
        )


class BajaUsuarioView(APIView):
    permission_classes = [EsAdministrador]

    @extend_schema(
        responses={204: None},
        description='Desactiva un usuario sin eliminarlo de la base.',
        tags=['Administración de usuarios'],
    )
    def delete(self, request, usuario_id):
        Usuario = get_user_model()
        usuario = get_object_or_404(Usuario, pk=usuario_id)

        if usuario.pk == request.user.pk:
            raise ValidationError({
                'usuario': 'No podés dar de baja tu propia cuenta.'
            })

        usuario.is_active = False
        usuario.save(update_fields=['is_active'])

        return Response(status=status.HTTP_204_NO_CONTENT)
