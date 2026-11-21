"""Reserva de un turno: junta las reglas puras de `services.py` con la base de datos."""

from django.db import IntegrityError, transaction

from catalogo.models import Box, Tarifa
from turnos.estados import ESTADOS_QUE_OCUPAN_BOX
from turnos.models import Turno, TurnoServicio
from turnos.services import (
    DatosInvalidos,
    SinBoxLibre,
    TarifaAplicada,
    elegir_box,
    planificar_turno,
)

# Si dos clientes reservan a la vez, la base rechaza al segundo con un IntegrityError
# (restricción de superposición). Entonces se vuelve a buscar un box libre.
INTENTOS_DE_ASIGNACION = 3


def _tarifas_aplicadas(vehiculo, servicios):
    """La tarifa de cada servicio para el tipo de vehículo. Error si falta alguna."""
    tarifas = {
        t.servicio_id: t
        for t in Tarifa.objects.filter(servicio__in=servicios, tipo_vehiculo=vehiculo.tipo)
    }
    sin_tarifa = [s.nombre for s in servicios if s.id not in tarifas]
    if sin_tarifa:
        raise DatosInvalidos(
            f'No hay tarifa para {vehiculo.get_tipo_display().lower()} en: '
            f'{", ".join(sin_tarifa)}.',
            campo='servicios',
        )
    return [
        TarifaAplicada(s.id, tarifas[s.id].precio, tarifas[s.id].duracion_minutos)
        for s in servicios
    ]


def _boxes_ocupados(inicio, fin):
    """Ids de los boxes con un turno (no cancelado) que se superpone con [inicio, fin)."""
    return set(
        Turno.objects.filter(
            estado__in=ESTADOS_QUE_OCUPAN_BOX,
            inicio__lt=fin,
            fin__gt=inicio,
        ).values_list('box_id', flat=True)
    )


def reservar_turno(vehiculo, servicios, inicio, ahora=None):
    """Crea un turno pendiente y devuelve el `Turno`.

    El precio, el fin y el box los calcula el backend. Puede lanzar `DatosInvalidos`
    (400) o `SinBoxLibre` (409).
    """
    plan = planificar_turno(_tarifas_aplicadas(vehiculo, servicios), inicio, ahora)

    for _ in range(INTENTOS_DE_ASIGNACION):
        try:
            with transaction.atomic():
                box_id = elegir_box(
                    Box.objects.filter(activo=True).values_list('id', flat=True),
                    _boxes_ocupados(inicio, plan.fin),
                )
                turno = Turno.objects.create(
                    vehiculo=vehiculo,
                    box_id=box_id,
                    inicio=inicio,
                    fin=plan.fin,
                    precio_total=plan.precio_total,
                )
                TurnoServicio.objects.bulk_create(
                    TurnoServicio(
                        turno=turno,
                        servicio_id=t.servicio_id,
                        precio=t.precio,
                        duracion_minutos=t.duracion_min,
                    )
                    for t in plan.tarifas
                )
            return turno
        except IntegrityError:
            continue

    raise SinBoxLibre('No hay ningún box libre en ese horario.')