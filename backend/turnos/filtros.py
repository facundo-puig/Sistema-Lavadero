"""Filtros de `GET /api/turnos/`: `fecha` (día en hora de Argentina), `box` y `estado`.

Un valor inválido devuelve 400 con el mensaje en el campo que corresponde.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import django_filters
from django import forms
from django.conf import settings

from turnos.estados import Estado
from turnos.models import Turno


class FiltroDeId(django_filters.Filter):
    """Acepta solo números enteros (un id), no decimales."""

    field_class = forms.IntegerField


class TurnoFilter(django_filters.FilterSet):
    fecha = django_filters.DateFilter(
        method='filtrar_por_fecha',
        error_messages={'invalid': 'Fecha inválida. Usá el formato 2026-11-20.'},
    )
    box = FiltroDeId(
        field_name='box_id',
        error_messages={'invalid': 'El box tiene que ser un número (el id del box).'},
    )
    estado = django_filters.ChoiceFilter(
        choices=Estado.choices,
        error_messages={'invalid_choice': '"%(value)s" no es un estado válido.'},
    )

    class Meta:
        model = Turno
        fields = []

    def filtrar_por_fecha(self, queryset, nombre, dia):
        # El día va de 00:00 a 24:00 en hora de Argentina, aunque en la base esté en UTC.
        zona = ZoneInfo(settings.TIMEZONE_NEGOCIO)
        desde = datetime.combine(dia, time.min, tzinfo=zona)
        hasta = datetime.combine(dia + timedelta(days=1), time.min, tzinfo=zona)
        return queryset.filter(inicio__gte=desde, inicio__lt=hasta)