
from django.contrib.auth import authenticate, get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken


def iniciar_sesion(email, password):
    Usuario = get_user_model()
    email = email.strip().lower()

    usuario = Usuario.objects.filter(email__iexact=email).first()

    if usuario is None or not usuario.is_active:
        raise AuthenticationFailed('Credenciales incorrectas.')

    usuario_autenticado = authenticate(
        username=usuario.username,
        password=password,
    )

    if usuario_autenticado is None:
        raise AuthenticationFailed('Credenciales incorrectas.')

    refresh = RefreshToken.for_user(usuario_autenticado)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'usuario': {
            'id': usuario_autenticado.id,
            'email': usuario_autenticado.email,
            'rol': usuario_autenticado.rol,
        },
    }
