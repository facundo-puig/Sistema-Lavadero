from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, viewsets

from catalogo.models import Box, Servicio, Tarifa, Vehiculo
from catalogo.serializers import (
    BoxSerializer,
    ServicioCatalogoSerializer,
    ServicioSerializer,
    VehiculoSerializer,
    servicios_con_tarifas,
)
from usuarios.permisos import EsAdministrador, EsCliente


@extend_schema(
    summary='Catálogo para reservar',
    description=(
        'Servicios activos con su tarifa (precio y duración) por tipo de vehículo, '
        'ordenados por nombre. Devuelve la lista completa, sin paginar.'
    ),
)
class CatalogoView(generics.ListAPIView):
    permission_classes = [EsCliente]
    serializer_class = ServicioCatalogoSerializer
    pagination_class = None

    def get_queryset(self):
        tarifas = Tarifa.objects.order_by('id')
        return (
            Servicio.objects.filter(activo=True)
            .prefetch_related(Prefetch('tarifas', queryset=tarifas))
            .order_by('nombre')
        )


@extend_schema_view(
    list=extend_schema(
        summary='Listar mis vehículos',
        description='Solo los vehículos activos del cliente, paginados de a 20.',
    ),
    create=extend_schema(
        summary='Registrar un vehículo',
        description=(
            'La patente se normaliza (mayúsculas, sin espacios ni guiones) y es única en '
            'todo el sistema. El dueño es siempre el usuario de la sesión.'
        ),
    ),
    retrieve=extend_schema(
        summary='Detalle de un vehículo',
        description='Devuelve 404 si no existe o es de otro cliente.',
    ),
    update=extend_schema(summary='Reemplazar patente y tipo de un vehículo'),
    partial_update=extend_schema(summary='Editar patente y/o tipo de un vehículo'),
    destroy=extend_schema(
        summary='Dar de baja un vehículo',
        description=(
            'Baja lógica (activo=false): la fila no se borra y los turnos que ya lo '
            'referencian se conservan.'
        ),
    ),
)
class VehiculoViewSet(viewsets.ModelViewSet):
    permission_classes = [EsCliente]
    serializer_class = VehiculoSerializer
    queryset = Vehiculo.objects.all()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Vehiculo.objects.none()
        # Un cliente nunca ve (ni sabe que existe) un vehículo de otro: da 404.
        vehiculos = Vehiculo.objects.filter(cliente=self.request.user).order_by('id')
        if self.action == 'list':
            # El listado solo muestra los activos; el detalle y la baja alcanzan
            # también a los inactivos, para que DELETE repetido siga dando 204.
            vehiculos = vehiculos.filter(activo=True)
        return vehiculos

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user)

    def perform_destroy(self, instance):
        if instance.activo:
            instance.activo = False
            instance.save(update_fields=['activo'])


class AltaYBajaLogicaMixin:
    """Alta siempre activa y DELETE como baja lógica (activo=False), sin borrar la fila."""

    def perform_create(self, serializer):
        serializer.save(activo=True)

    def perform_destroy(self, instance):
        if instance.activo:
            instance.activo = False
            instance.save(update_fields=['activo'])


@extend_schema_view(
    list=extend_schema(
        summary='Listar servicios',
        description=(
            'Servicios con sus tarifas por tipo de vehículo. Filtro opcional '
            '`?activo=true` o `?activo=false`. Paginado de a 20.'
        ),
    ),
    create=extend_schema(
        summary='Crear un servicio',
        description=(
            'Crea el servicio (siempre activo) junto con sus tarifas. No se puede '
            'repetir el tipo de vehículo; precio y duración tienen que ser mayores a 0.'
        ),
    ),
    retrieve=extend_schema(summary='Detalle de un servicio'),
    update=extend_schema(
        summary='Reemplazar un servicio',
        description=(
            'Exige el nombre. Si se envían tarifas, cada una se crea o se actualiza '
            'según su tipo de vehículo; las que no se envían quedan como están.'
        ),
    ),
    partial_update=extend_schema(
        summary='Editar un servicio',
        description=(
            'Acepta nombre, descripción, activo y tarifas. Las tarifas se crean o se '
            'actualizan por tipo de vehículo y nunca se eliminan.'
        ),
    ),
    destroy=extend_schema(
        summary='Dar de baja un servicio',
        description=(
            'Baja lógica (activo=false): la fila y sus tarifas no se borran y los turnos '
            'que ya lo referencian se conservan.'
        ),
    ),
)
class ServicioViewSet(AltaYBajaLogicaMixin, viewsets.ModelViewSet):
    permission_classes = [EsAdministrador]
    serializer_class = ServicioSerializer
    queryset = Servicio.objects.all()
    filterset_fields = ['activo']

    def get_queryset(self):
        return servicios_con_tarifas().order_by('id')


@extend_schema_view(
    list=extend_schema(
        summary='Listar boxes',
        description='Filtro opcional `?activo=true` o `?activo=false`. Paginado de a 20.',
    ),
    create=extend_schema(
        summary='Crear un box',
        description='El nombre es obligatorio y único. El box se crea siempre activo.',
    ),
    retrieve=extend_schema(summary='Detalle de un box'),
    update=extend_schema(summary='Reemplazar un box (exige el nombre)'),
    partial_update=extend_schema(summary='Editar el nombre y/o el estado de un box'),
    destroy=extend_schema(
        summary='Dar de baja un box',
        description=(
            'Baja lógica (activo=false): la fila no se borra y los turnos que ya lo '
            'usan se conservan.'
        ),
    ),
)
class BoxViewSet(AltaYBajaLogicaMixin, viewsets.ModelViewSet):
    permission_classes = [EsAdministrador]
    serializer_class = BoxSerializer
    queryset = Box.objects.all()
    filterset_fields = ['activo']

    def get_queryset(self):
        return Box.objects.order_by('id')
