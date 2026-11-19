from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from catalogo.models import Servicio, Tarifa, Vehiculo
from catalogo.serializers import ServicioCatalogoSerializer, VehiculoSerializer


@extend_schema(
    summary='Catálogo para reservar',
    description=(
        'Servicios activos con su tarifa (precio y duración) por tipo de vehículo, '
        'ordenados por nombre. Devuelve la lista completa, sin paginar.'
    ),
)
class CatalogoView(generics.ListAPIView):
    # TODO: solo para clientes: cuando se mergee `usuarios/permisos.py` (HU-A4),
    # usar EsCliente.
    permission_classes = [IsAuthenticated]
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
    # TODO: solo para clientes: cuando se mergee `usuarios/permisos.py` (HU-A4),
    # usar EsCliente.
    permission_classes = [IsAuthenticated]
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
