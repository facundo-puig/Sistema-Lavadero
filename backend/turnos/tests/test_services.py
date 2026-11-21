"""Tests de las reglas de negocio de los turnos (no necesitan base de datos)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from turnos.estados import ESTADOS_QUE_OCUPAN_BOX, Estado
from turnos.services import (
    DatosInvalidos,
    SinBoxLibre,
    TarifaAplicada,
    TransicionInvalida,
    calcular_fin,
    calcular_totales,
    elegir_box,
    planificar_turno,
    se_superponen,
    validar_cancelacion,
    validar_horario,
    validar_transicion,
)

ARGENTINA = ZoneInfo('America/Argentina/Buenos_Aires')
AHORA = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


def en_argentina(hora, minuto=0, dia=20):
    """Un instante del 2026-11 a la hora de Argentina indicada, expresado en UTC."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ARGENTINA).astimezone(UTC)


def tarifa(servicio_id, precio, duracion_min):
    return TarifaAplicada(servicio_id, Decimal(precio), duracion_min)


# ---------------------------------------------------------------------------
# Regla 2: precio y fin calculados por el backend
# ---------------------------------------------------------------------------


def test_el_precio_es_la_suma_de_las_tarifas_y_la_duracion_la_suma_de_minutos():
    precio, duracion = calcular_totales([tarifa(1, '9000.00', 45), tarifa(2, '3500.00', 30)])

    assert precio == Decimal('12500.00')
    assert duracion == 75


def test_el_precio_no_arrastra_errores_de_decimales():
    precio, _ = calcular_totales([tarifa(1, '0.10', 10), tarifa(2, '0.20', 10)])

    assert precio == Decimal('0.30')


def test_sin_servicios_es_un_error_del_campo_servicios():
    with pytest.raises(DatosInvalidos) as error:
        calcular_totales([])

    assert error.value.codigo_http == 400
    assert error.value.detalle == {'servicios': ['Elegí al menos un servicio.']}


def test_no_se_puede_repetir_un_servicio():
    with pytest.raises(DatosInvalidos) as error:
        calcular_totales([tarifa(1, '100.00', 10), tarifa(1, '100.00', 10)])

    assert error.value.campo == 'servicios'


def test_el_fin_es_el_inicio_mas_la_duracion():
    inicio = en_argentina(10)

    assert calcular_fin(inicio, 75) == inicio + timedelta(minutes=75)


def test_planificar_turno_devuelve_precio_y_fin_como_el_ejemplo_del_contrato():
    plan = planificar_turno(
        [tarifa(1, '9000.00', 45), tarifa(2, '3500.00', 30)],
        inicio=datetime(2026, 11, 20, 13, 0, tzinfo=UTC),
        ahora=AHORA,
    )

    assert plan.precio_total == Decimal('12500.00')
    assert plan.duracion_min == 75
    assert plan.fin == datetime(2026, 11, 20, 14, 15, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Horario de atención (8:00 a 20:00, hora de Argentina) y turno futuro
# ---------------------------------------------------------------------------


def test_un_turno_dentro_del_horario_es_valido():
    validar_horario(en_argentina(10), en_argentina(11), AHORA)


def test_puede_empezar_justo_a_la_apertura_y_terminar_justo_al_cierre():
    validar_horario(en_argentina(8), en_argentina(9), AHORA)
    validar_horario(en_argentina(19), en_argentina(20), AHORA)


def test_el_horario_se_evalua_en_hora_de_argentina_y_no_en_utc():
    # 11:00 UTC son las 8:00 en Argentina: es válido. 10:59 UTC serían las 7:59: no.
    validar_horario(
        datetime(2026, 11, 20, 11, 0, tzinfo=UTC),
        datetime(2026, 11, 20, 12, 0, tzinfo=UTC),
        AHORA,
    )
    with pytest.raises(DatosInvalidos):
        validar_horario(
            datetime(2026, 11, 20, 10, 59, tzinfo=UTC),
            datetime(2026, 11, 20, 11, 59, tzinfo=UTC),
            AHORA,
        )


def test_empezar_antes_de_la_apertura_es_invalido():
    with pytest.raises(DatosInvalidos) as error:
        validar_horario(en_argentina(7, 30), en_argentina(8, 30), AHORA)

    assert error.value.campo == 'inicio'
    assert 'horario de atención' in error.value.mensaje


def test_terminar_despues_del_cierre_es_invalido():
    with pytest.raises(DatosInvalidos) as error:
        validar_horario(en_argentina(19, 30), en_argentina(20, 1), AHORA)

    assert error.value.campo == 'inicio'
    assert 'Terminaría a las 20:01' in error.value.mensaje


def test_un_turno_que_cruza_la_medianoche_es_invalido():
    with pytest.raises(DatosInvalidos):
        validar_horario(en_argentina(23), en_argentina(23) + timedelta(hours=2), AHORA)


def test_un_turno_en_el_pasado_es_invalido():
    with pytest.raises(DatosInvalidos) as error:
        validar_horario(en_argentina(10, dia=10), en_argentina(11, dia=10), AHORA)

    assert error.value.detalle == {'inicio': ['El turno tiene que ser en el futuro.']}


def test_un_turno_que_empieza_ahora_mismo_no_es_futuro():
    with pytest.raises(DatosInvalidos):
        validar_horario(AHORA, AHORA + timedelta(hours=1), AHORA)


def test_las_fechas_sin_zona_horaria_se_rechazan():
    with pytest.raises(ValueError):
        validar_horario(datetime(2026, 11, 20, 13, 0), datetime(2026, 11, 20, 14, 0), AHORA)


def test_planificar_turno_rechaza_un_turno_que_termina_despues_del_cierre():
    # 19:00 + 90 minutos = 20:30
    with pytest.raises(DatosInvalidos):
        planificar_turno([tarifa(1, '9000.00', 90)], inicio=en_argentina(19), ahora=AHORA)


# ---------------------------------------------------------------------------
# Regla 1: superposición y asignación de box
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('inicio_b', 'fin_b', 'esperado'),
    [
        (10, 11, True),  # mismo horario
        (9, 11, True),  # el otro empieza antes y se solapa
        (10, 12, True),  # el otro termina después y se solapa
        (9, 12, True),  # el otro lo contiene
        (11, 12, False),  # empieza justo cuando termina: no se superpone
        (8, 10, False),  # termina justo cuando empieza: no se superpone
        (13, 14, False),  # separados
    ],
)
def test_se_superponen_con_intervalos_semiabiertos(inicio_b, fin_b, esperado):
    resultado = se_superponen(
        en_argentina(10), en_argentina(11), en_argentina(inicio_b), en_argentina(fin_b)
    )

    assert resultado is esperado


def test_se_asigna_el_primer_box_libre_por_id():
    assert elegir_box([3, 1, 2], ocupados={1}) == 2


def test_si_todos_los_boxes_estan_libres_se_asigna_el_de_menor_id():
    assert elegir_box([2, 1], ocupados=set()) == 1


def test_sin_box_libre_es_un_conflicto_409():
    with pytest.raises(SinBoxLibre) as error:
        elegir_box([1, 2], ocupados={1, 2})

    assert error.value.codigo_http == 409
    assert error.value.detalle == {'detail': 'No hay ningún box libre en ese horario.'}


def test_sin_boxes_activos_tambien_es_un_conflicto():
    with pytest.raises(SinBoxLibre):
        elegir_box([], ocupados=set())


def test_un_turno_cancelado_no_ocupa_box():
    assert Estado.CANCELADO not in ESTADOS_QUE_OCUPAN_BOX
    assert Estado.PENDIENTE in ESTADOS_QUE_OCUPAN_BOX


# ---------------------------------------------------------------------------
# Regla 3: flujo de estados
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('actual', 'nuevo'),
    [
        ('pendiente', 'en_proceso'),
        ('en_proceso', 'finalizado'),
        ('finalizado', 'entregado'),
    ],
)
def test_se_puede_avanzar_un_paso(actual, nuevo):
    assert validar_transicion(actual, nuevo) == Estado(nuevo)


@pytest.mark.parametrize(
    ('actual', 'nuevo'),
    [
        ('pendiente', 'finalizado'),  # salto
        ('pendiente', 'entregado'),  # salto
        ('en_proceso', 'entregado'),  # salto
        ('en_proceso', 'pendiente'),  # retroceso
        ('finalizado', 'en_proceso'),  # retroceso
        ('pendiente', 'pendiente'),  # mismo estado
        ('entregado', 'finalizado'),  # estado final
        ('cancelado', 'pendiente'),  # estado final
        ('cancelado', 'en_proceso'),  # estado final
    ],
)
def test_no_se_permiten_saltos_retrocesos_ni_cambios_desde_un_estado_final(actual, nuevo):
    with pytest.raises(TransicionInvalida) as error:
        validar_transicion(actual, nuevo)

    assert error.value.codigo_http == 400
    assert error.value.campo == 'estado'


def test_el_mensaje_de_transicion_invalida_es_el_del_contrato():
    with pytest.raises(TransicionInvalida) as error:
        validar_transicion('pendiente', 'finalizado')

    assert error.value.detalle == {
        'estado': ["No se puede pasar de 'pendiente' a 'finalizado'. Permitido: 'en_proceso'."]
    }


@pytest.mark.parametrize('actual', ['pendiente', 'en_proceso', 'finalizado'])
def test_cancelar_no_se_hace_con_el_cambio_de_estado(actual):
    with pytest.raises(TransicionInvalida):
        validar_transicion(actual, 'cancelado')


def test_un_estado_inexistente_no_es_valido():
    with pytest.raises(ValueError):
        validar_transicion('pendiente', 'volando')


# ---------------------------------------------------------------------------
# Regla 3 (cancelación): solo se cancela un turno pendiente
# ---------------------------------------------------------------------------


def test_se_puede_cancelar_un_turno_pendiente():
    assert validar_cancelacion('pendiente') == Estado.CANCELADO


@pytest.mark.parametrize('actual', ['en_proceso', 'finalizado', 'entregado', 'cancelado'])
def test_no_se_puede_cancelar_un_turno_que_no_esta_pendiente(actual):
    with pytest.raises(TransicionInvalida) as error:
        validar_cancelacion(actual)

    assert error.value.detalle == {'detail': 'Solo se puede cancelar un turno pendiente.'}