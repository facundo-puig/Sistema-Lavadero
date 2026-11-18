from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models
from django.db.models import F, Func, Q

from turnos.estados import Estado


class RangoDeTiempo(Func):
    """Rango [inicio, fin) de Postgres (`tstzrange`), para la restricción de superposición."""

    function = 'TSTZRANGE'
    output_field = DateTimeRangeField()


class Turno(models.Model):
    vehiculo = models.ForeignKey(
        'catalogo.Vehiculo',
        on_delete=models.PROTECT,
        related_name='turnos',
    )
    box = models.ForeignKey(
        'catalogo.Box',
        on_delete=models.PROTECT,
        related_name='turnos',
    )
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['inicio']
        indexes = [
            models.Index(fields=['inicio'], name='turno_inicio_idx'),
            models.Index(fields=['estado', 'inicio'], name='turno_estado_inicio_idx'),
        ]
        constraints = [
            # Regla 1: dos turnos no cancelados no se superponen en el mismo box.
            # La garantiza la base de datos, no solo la vista. Los rangos son [inicio, fin):
            # un turno que empieza justo cuando termina otro no se superpone.
            ExclusionConstraint(
                name='turno_sin_superposicion_en_box',
                expressions=[
                    (RangoDeTiempo(F('inicio'), F('fin')), RangeOperators.OVERLAPS),
                    ('box', RangeOperators.EQUAL),
                ],
                condition=~Q(estado=Estado.CANCELADO),
            ),
            models.CheckConstraint(
                condition=Q(fin__gt=F('inicio')),
                name='turno_fin_posterior_al_inicio',
            ),
            models.CheckConstraint(
                condition=Q(precio_total__gte=0),
                name='turno_precio_total_no_negativo',
            ),
        ]

    def __str__(self):
        return f'Turno {self.pk} - {self.vehiculo} - {self.inicio:%Y-%m-%d %H:%M}'


class TurnoServicio(models.Model):
    """Un servicio contratado en un turno, con el precio y la duración al reservar.

    Guarda una copia de la tarifa: si después el administrador cambia los precios,
    los turnos ya reservados no se modifican.
    """

    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        related_name='servicios',
    )
    servicio = models.ForeignKey(
        'catalogo.Servicio',
        on_delete=models.PROTECT,
        related_name='turnos',
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['turno', 'servicio'],
                name='turnoservicio_unico_por_turno_y_servicio',
            ),
            models.CheckConstraint(
                condition=Q(duracion_minutos__gt=0),
                name='turnoservicio_duracion_mayor_a_cero',
            ),
        ]

    def __str__(self):
        return f'{self.turno_id} - {self.servicio}'