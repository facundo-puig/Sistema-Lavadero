"""Reglas de negocio de los turnos.

Son funciones puras: no leen la request ni la base de datos, así que se prueban sin
levantar nada. Las vistas (y los serializers) las llaman y traducen los errores a HTTP.

Los errores llevan `codigo_http` y `detalle`, que ya tiene la forma que define
`docs/api-turnos.md`: `{"campo": ["mensaje"]}` o `{"detail": "mensaje"}`.
"""

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from turnos.estados import SIGUIENTE_ESTADO, Estado


class ErrorDeTurno(Exception):
    """Base de los errores de las reglas de turnos."""

    codigo_http = 400

    def __init__(self, mensaje, campo=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo

    @property
    def detalle(self):
        if self.campo:
            return {self.campo: [self.mensaje]}
        return {'detail': self.mensaje}


class DatosInvalidos(ErrorDeTurno):
    """Los datos del pedido no cumplen una regla (HTTP 400)."""


class TransicionInvalida(ErrorDeTurno):
    """El cambio de estado o la cancelación no están permitidos (HTTP 400)."""


class SinBoxLibre(ErrorDeTurno):
    """Ningún box activo está libre en el horario pedido (HTTP 409)."""

    codigo_http = 409


@dataclass(frozen=True)
class TarifaAplicada:
    """Precio y duración de un servicio para el tipo de vehículo del turno."""

    servicio_id: int
    precio: Decimal
    duracion_min: int


@dataclass(frozen=True)
class PlanDeTurno:
    """Lo que el backend calcula a partir de lo que elige el cliente."""

    fin: datetime
    precio_total: Decimal
    duracion_min: int
    tarifas: tuple[TarifaAplicada, ...]


# ---------------------------------------------------------------------------
# Cálculo de precio y fin
# ---------------------------------------------------------------------------


def calcular_totales(tarifas: Iterable[TarifaAplicada]) -> tuple[Decimal, int]:
    """Suma de precios y de duraciones (en minutos) de los servicios elegidos."""
    tarifas = list(tarifas)
    if not tarifas:
        raise DatosInvalidos('Elegí al menos un servicio.', campo='servicios')

    ids = [t.servicio_id for t in tarifas]
    if len(ids) != len(set(ids)):
        raise DatosInvalidos('No se puede repetir un servicio.', campo='servicios')

    precio_total = sum((t.precio for t in tarifas), Decimal(0)).quantize(Decimal('0.01'))
    duracion_min = sum(t.duracion_min for t in tarifas)
    return precio_total, duracion_min


def calcular_fin(inicio: datetime, duracion_min: int) -> datetime:
    """Hora de fin: el inicio más la duración total."""
    return inicio + timedelta(minutes=duracion_min)


# ---------------------------------------------------------------------------
# Horario de atención
# ---------------------------------------------------------------------------


def validar_horario(inicio: datetime, fin: datetime, ahora: datetime | None = None) -> None:
    """El turno tiene que ser futuro y estar entero dentro del horario de atención.

    El horario se evalúa en hora de Argentina (`settings.TIMEZONE_NEGOCIO`), aunque las
    fechas viajen y se guarden en UTC. Puede terminar justo a la hora de cierre.
    """
    if timezone.is_naive(inicio) or timezone.is_naive(fin):
        raise ValueError('inicio y fin tienen que tener zona horaria (UTC).')

    ahora = ahora or timezone.now()
    if inicio <= ahora:
        raise DatosInvalidos('El turno tiene que ser en el futuro.', campo='inicio')

    zona = ZoneInfo(settings.TIMEZONE_NEGOCIO)
    inicio_local = inicio.astimezone(zona)
    fin_local = fin.astimezone(zona)
    desde = settings.HORARIO_ATENCION_DESDE
    hasta = settings.HORARIO_ATENCION_HASTA

    dentro_del_horario = (
        inicio_local.time() >= desde
        and fin_local.date() == inicio_local.date()
        and fin_local.time() <= hasta
    )
    if not dentro_del_horario:
        raise DatosInvalidos(
            f'El turno tiene que estar dentro del horario de atención '
            f'({desde:%H:%M} a {hasta:%H:%M}). Terminaría a las {fin_local:%H:%M}.',
            campo='inicio',
        )


def planificar_turno(
    tarifas: Iterable[TarifaAplicada],
    inicio: datetime,
    ahora: datetime | None = None,
) -> PlanDeTurno:
    """Punto de entrada de la reserva: calcula precio y fin, y valida el horario."""
    tarifas = tuple(tarifas)
    precio_total, duracion_min = calcular_totales(tarifas)
    fin = calcular_fin(inicio, duracion_min)
    validar_horario(inicio, fin, ahora)
    return PlanDeTurno(
        fin=fin,
        precio_total=precio_total,
        duracion_min=duracion_min,
        tarifas=tarifas,
    )


# ---------------------------------------------------------------------------
# Superposición y asignación de box
# ---------------------------------------------------------------------------


def se_superponen(
    inicio_a: datetime,
    fin_a: datetime,
    inicio_b: datetime,
    fin_b: datetime,
) -> bool:
    """Dos turnos se superponen si comparten algún instante.

    Los intervalos son semiabiertos `[inicio, fin)`: un turno que empieza justo cuando
    termina otro NO se superpone. Es la misma semántica que usa la base de datos.
    """
    return inicio_a < fin_b and inicio_b < fin_a


def elegir_box(box_ids: Iterable[int], ocupados: Collection[int]) -> int:
    """El primer box (por id) que no está ocupado. Si no hay ninguno, error 409."""
    for box_id in sorted(box_ids):
        if box_id not in ocupados:
            return box_id
    raise SinBoxLibre('No hay ningún box libre en ese horario.')


# ---------------------------------------------------------------------------
# Estados
# ---------------------------------------------------------------------------


def validar_transicion(actual: str, nuevo: str) -> Estado:
    """Valida un cambio de estado del flujo y devuelve el nuevo estado.

    Solo se avanza un paso: pendiente → en_proceso → finalizado → entregado.
    Cancelar tiene su propia regla (`validar_cancelacion`).
    """
    actual = Estado(actual)
    nuevo = Estado(nuevo)

    if nuevo == Estado.CANCELADO:
        raise TransicionInvalida(
            'Para cancelar un turno hay que usar la cancelación, no el cambio de estado.',
            campo='estado',
        )

    permitido = SIGUIENTE_ESTADO.get(actual)
    if permitido is None:
        raise TransicionInvalida(
            f"No se puede pasar de '{actual.value}' a '{nuevo.value}'. "
            f"Un turno '{actual.value}' ya no admite cambios de estado.",
            campo='estado',
        )
    if nuevo != permitido:
        raise TransicionInvalida(
            f"No se puede pasar de '{actual.value}' a '{nuevo.value}'. "
            f"Permitido: '{permitido.value}'.",
            campo='estado',
        )
    return nuevo


def validar_cancelacion(actual: str) -> Estado:
    """Solo se puede cancelar un turno pendiente. Devuelve el estado `cancelado`."""
    if Estado(actual) != Estado.PENDIENTE:
        raise TransicionInvalida('Solo se puede cancelar un turno pendiente.')
    return Estado.CANCELADO