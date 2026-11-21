"""Resumen de turnos e ingresos de un período: `GET /api/resumen/` (solo administrador)."""

from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Count, Sum
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from turnos.estados import Estado
from turnos.models import Turno
from usuarios.permisos import EsAdministrador

# Los ingresos suman solo los turnos que ya se hicieron.
ESTADOS_QUE_FACTURAN = (Estado.FINALIZADO, Estado.ENTREGADO)


class PeriodoSerializer(serializers.Serializer):
    """Parámetros de la consulta: `desde` y `hasta`, ambos incluidos."""

    desde = serializers.DateField(
        error_messages={
            'required': 'Indicá la fecha desde (por ejemplo, 2026-11-01).',
            'null': 'Indicá la fecha desde (por ejemplo, 2026-11-01).',
            'invalid': 'Fecha inválida. Usá el formato 2026-11-01.',
        },
    )
    hasta = serializers.DateField(
        error_messages={
            'required': 'Indicá la fecha hasta (por ejemplo, 2026-11-30).',
            'null': 'Indicá la fecha hasta (por ejemplo, 2026-11-30).',
            'invalid': 'Fecha inválida. Usá el formato 2026-11-30.',
        },
    )

    def validate(self, datos):
        if datos['desde'] > datos['hasta']:
            raise serializers.ValidationError(
                {'desde': 'La fecha desde no puede ser posterior a la fecha hasta.'}
            )
        return datos


class ResumenSerializer(serializers.Serializer):
    """Forma de la respuesta (solo para la documentación de Swagger)."""

    desde = serializers.DateField()
    hasta = serializers.DateField()
    turnos_por_estado = serializers.DictField(child=serializers.IntegerField())
    ingresos_total = serializers.CharField()


def calcular_resumen(desde, hasta):
    """Cuenta los turnos por estado y suma los ingresos entre dos días (ambos incluidos).

    Los días son los de Argentina; en la base los turnos están en UTC.
    """
    zona = ZoneInfo(settings.TIMEZONE_NEGOCIO)
    desde_utc = datetime.combine(desde, time.min, tzinfo=zona)
    hasta_utc = datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=zona)
    turnos = Turno.objects.filter(inicio__gte=desde_utc, inicio__lt=hasta_utc)

    # Todos los estados aparecen en la respuesta, aunque no tengan turnos.
    por_estado = {estado.value: 0 for estado in Estado}
    for fila in turnos.values('estado').annotate(cantidad=Count('id')):
        por_estado[fila['estado']] = fila['cantidad']

    total = turnos.filter(estado__in=ESTADOS_QUE_FACTURAN).aggregate(total=Sum('precio_total'))
    ingresos = (total['total'] or Decimal(0)).quantize(Decimal('0.01'))

    return {
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'turnos_por_estado': por_estado,
        'ingresos_total': str(ingresos),
    }


class ResumenView(APIView):
    permission_classes = [EsAdministrador]

    @extend_schema(
        summary='Resumen de turnos e ingresos',
        description=(
            'Cantidad de turnos por estado e ingresos (turnos finalizados y entregados) '
            'entre `desde` y `hasta`, ambos incluidos, en hora de Argentina. '
            'Los dos parámetros son obligatorios.'
        ),
        parameters=[PeriodoSerializer],
        responses={200: ResumenSerializer},
    )
    def get(self, request):
        periodo = PeriodoSerializer(data=request.query_params)
        periodo.is_valid(raise_exception=True)
        return Response(calcular_resumen(**periodo.validated_data))