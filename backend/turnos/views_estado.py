"""Cambio de estado de un turno: `PATCH /api/turnos/{id}/estado/`."""

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from turnos.estados import Estado
from turnos.models import Turno, TurnoServicio
from turnos.serializers import TurnoSerializer
from turnos.services import ErrorDeTurno, validar_transicion
from usuarios.permisos import EsAdministradorOOperario


class CambioDeEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(
        choices=Estado.choices,
        error_messages={'invalid_choice': '"{input}" no es un estado válido.'},
    )


class CambiarEstadoView(APIView):
    """Avanza un turno un paso en el flujo. Solo administrador y operario."""

    permission_classes = [EsAdministradorOOperario]

    @extend_schema(
        summary='Avanzar el estado de un turno',
        description=(
            'Solo acepta el siguiente estado del flujo: pendiente → en_proceso → finalizado → '
            'entregado. Para cancelar se usa `POST /api/turnos/{id}/cancelar/`.'
        ),
        request=CambioDeEstadoSerializer,
        responses={200: TurnoSerializer},
    )
    def patch(self, request, pk):
        entrada = CambioDeEstadoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        nuevo = entrada.validated_data['estado']

        with transaction.atomic():
            # Se bloquea la fila para que dos cambios simultáneos no salten un paso.
            turno = get_object_or_404(Turno.objects.select_for_update(), pk=pk)
            try:
                turno.estado = validar_transicion(turno.estado, nuevo)
            except ErrorDeTurno as error:
                return Response(error.detalle, status=error.codigo_http)
            turno.save(update_fields=['estado'])

        turno = (
            Turno.objects.select_related('vehiculo', 'box')
            .prefetch_related(
                Prefetch('servicios', queryset=TurnoServicio.objects.select_related('servicio'))
            )
            .get(pk=turno.pk)
        )
        return Response(TurnoSerializer(turno).data)