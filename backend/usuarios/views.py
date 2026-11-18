
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import LoginRespuestaSerializer, LoginSerializer
from .services import iniciar_sesion


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
