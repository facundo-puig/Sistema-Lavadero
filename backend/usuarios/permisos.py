
from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    message = 'Solo los administradores pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == 'ADMINISTRADOR'
        )


class EsOperario(BasePermission):
    message = 'Solo los operarios pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == 'OPERARIO'
        )


class EsCliente(BasePermission):
    message = 'Solo los clientes pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == 'CLIENTE'
        )


class EsAdministradorOOperario(BasePermission):
    message = 'Solo administradores y operarios pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol in ('ADMINISTRADOR', 'OPERARIO')
        )
