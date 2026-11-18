from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from catalogo.models import Servicio, Tarifa
from catalogo.serializers import ServicioCatalogoSerializer


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
