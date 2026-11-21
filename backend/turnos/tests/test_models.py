"""Tests de los modelos de turnos. Necesitan Postgres: la restricción de superposición
(`ExclusionConstraint`) no existe en SQLite."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from turnos.estados import Estado
from turnos.models import Turno, TurnoServicio

pytestmark = pytest.mark.django_db


def hora(hh, mm=0):
    """Un instante del 20/11/2026 en UTC (estos tests no dependen de la hora de Argentina)."""
    return datetime(2026, 11, 20, hh, mm, tzinfo=UTC)


def test_un_turno_nuevo_queda_pendiente(crear_turno):
    turno = crear_turno()

    assert turno.estado == Estado.PENDIENTE


# ---------------------------------------------------------------------------
# Regla 1: no superposición en un box, garantizada por la base de datos
# ---------------------------------------------------------------------------


def test_no_se_puede_crear_un_turno_que_se_superpone_en_el_mismo_box(crear_turno):
    crear_turno(inicio=hora(13), fin=hora(14))

    with pytest.raises(IntegrityError), transaction.atomic():
        crear_turno(inicio=hora(13, 30), fin=hora(14, 30))


def test_no_se_puede_crear_un_turno_dentro_de_otro_en_el_mismo_box(crear_turno):
    crear_turno(inicio=hora(13), fin=hora(16))

    with pytest.raises(IntegrityError), transaction.atomic():
        crear_turno(inicio=hora(14), fin=hora(15))


def test_dos_turnos_pueden_ser_consecutivos_en_el_mismo_box(crear_turno):
    crear_turno(inicio=hora(13), fin=hora(14))

    crear_turno(inicio=hora(14), fin=hora(15))
    crear_turno(inicio=hora(12), fin=hora(13))

    assert Turno.objects.count() == 3


def test_el_mismo_horario_en_otro_box_es_valido(crear_turno, box_2):
    crear_turno(inicio=hora(13), fin=hora(14))

    crear_turno(inicio=hora(13), fin=hora(14), box=box_2)

    assert Turno.objects.count() == 2


def test_un_turno_cancelado_no_ocupa_el_box(crear_turno):
    crear_turno(inicio=hora(13), fin=hora(14), estado=Estado.CANCELADO)

    crear_turno(inicio=hora(13), fin=hora(14))

    assert Turno.objects.count() == 2


def test_al_cancelar_un_turno_su_horario_queda_libre(crear_turno):
    turno = crear_turno(inicio=hora(13), fin=hora(14))
    turno.estado = Estado.CANCELADO
    turno.save()

    crear_turno(inicio=hora(13), fin=hora(14))

    assert Turno.objects.filter(estado=Estado.PENDIENTE).count() == 1


def test_no_se_puede_reactivar_un_turno_si_su_horario_fue_ocupado(crear_turno):
    cancelado = crear_turno(inicio=hora(13), fin=hora(14), estado=Estado.CANCELADO)
    crear_turno(inicio=hora(13), fin=hora(14))

    cancelado.estado = Estado.PENDIENTE
    with pytest.raises(IntegrityError), transaction.atomic():
        cancelado.save()


@pytest.mark.parametrize('estado', [Estado.EN_PROCESO, Estado.FINALIZADO, Estado.ENTREGADO])
def test_los_turnos_en_curso_o_terminados_siguen_ocupando_el_box(crear_turno, estado):
    crear_turno(inicio=hora(13), fin=hora(14), estado=estado)

    with pytest.raises(IntegrityError), transaction.atomic():
        crear_turno(inicio=hora(13), fin=hora(14))


# ---------------------------------------------------------------------------
# Otras restricciones
# ---------------------------------------------------------------------------


def test_el_fin_tiene_que_ser_posterior_al_inicio(crear_turno):
    with pytest.raises(IntegrityError), transaction.atomic():
        crear_turno(inicio=hora(13), fin=hora(13))


def test_el_precio_total_no_puede_ser_negativo(crear_turno):
    turno = crear_turno()
    turno.precio_total = Decimal('-1.00')

    with pytest.raises(IntegrityError), transaction.atomic():
        turno.save()


def test_un_vehiculo_con_turnos_no_se_puede_borrar(crear_turno, vehiculo):
    crear_turno()

    with pytest.raises(ProtectedError):
        vehiculo.delete()


def test_un_box_con_turnos_no_se_puede_borrar(crear_turno, box_1):
    crear_turno()

    with pytest.raises(ProtectedError):
        box_1.delete()


# ---------------------------------------------------------------------------
# TurnoServicio: copia de la tarifa al reservar
# ---------------------------------------------------------------------------


def test_el_turno_guarda_el_precio_y_la_duracion_de_cada_servicio(crear_turno, servicio):
    turno = crear_turno()

    TurnoServicio.objects.create(
        turno=turno, servicio=servicio, precio=Decimal('6000.00'), duracion_minutos=30
    )

    item = turno.servicios.get()
    assert item.precio == Decimal('6000.00')
    assert item.duracion_minutos == 30


def test_un_servicio_no_se_puede_repetir_en_un_turno(crear_turno, servicio):
    turno = crear_turno()
    TurnoServicio.objects.create(
        turno=turno, servicio=servicio, precio=Decimal('6000.00'), duracion_minutos=30
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        TurnoServicio.objects.create(
            turno=turno, servicio=servicio, precio=Decimal('6000.00'), duracion_minutos=30
        )


def test_la_duracion_de_un_servicio_tiene_que_ser_mayor_a_cero(crear_turno, servicio):
    turno = crear_turno()

    with pytest.raises(IntegrityError), transaction.atomic():
        TurnoServicio.objects.create(
            turno=turno, servicio=servicio, precio=Decimal('6000.00'), duracion_minutos=0
        )


def test_un_servicio_con_turnos_no_se_puede_borrar(crear_turno, servicio):
    turno = crear_turno()
    TurnoServicio.objects.create(
        turno=turno, servicio=servicio, precio=Decimal('6000.00'), duracion_minutos=30
    )

    with pytest.raises(ProtectedError):
        servicio.delete()