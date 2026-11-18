from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from turnos.models import Turno, TurnoServicio
from turnos.reservas import reservar_turno
from turnos.serializers import ReservaSerializer, TurnoSerializer
from turnos.services import ErrorDeTurno


class TurnoViewSet(viewsets.GenericViewSet):
    # TODO: cambiar a [EsCliente] cuando se mergee `usuarios/permisos.py` (HU-A4).
    permission_classes = [IsAuthenticated]
    serializer_class = TurnoSerializer
    queryset = Turno.objects.all()

    def get_queryset(self):
        return Turno.objects.select_related('vehiculo', 'box').prefetch_related(
            Prefetch('servicios', queryset=TurnoServicio.objects.select_related('servicio'))
        )

    @extend_schema(
        summary='Reservar un turno',
        description=(
            'El cliente elige vehículo, servicios y horario de inicio. El backend calcula el '
            'precio total y la hora de fin, y asigna el primer box libre. '
            'Devuelve 409 si no hay ningún box libre en ese horario.'
        ),
        request=ReservaSerializer,
        responses={201: TurnoSerializer},
    )
    def create(self, request):
        entrada = ReservaSerializer(data=request.data, context={'request': request})
        entrada.is_valid(raise_exception=True)

        try:
            turno = reservar_turno(**entrada.validated_data)
        except ErrorDeTurno as error:
            return Response(error.detalle, status=error.codigo_http)

        turno = self.get_queryset().get(pk=turno.pk)
        return Response(TurnoSerializer(turno).data, status=status.HTTP_201_CREATED)