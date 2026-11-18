
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import (
    LoginRespuestaSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegistroRespuestaSerializer,
    RegistroSerializer,
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
