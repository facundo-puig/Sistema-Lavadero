from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdministracionUsuariosView,
    BajaUsuarioView,
    CambiarRolUsuarioView,
    LoginView,
    LogoutView,
    RegistroView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path(
        'usuarios/',
        AdministracionUsuariosView.as_view(),
        name='administracion-usuarios',
    ),
    path(
        'usuarios/<int:usuario_id>/rol/',
        CambiarRolUsuarioView.as_view(),
        name='cambiar-rol-usuario',
    ),
    path(
        'usuarios/<int:usuario_id>/',
        BajaUsuarioView.as_view(),
        name='baja-usuario',
    ),
]