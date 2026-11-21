from turnos.estados import Estado

# Mientras un turno está en alguno de estos estados, su precio y su duración
# dependen del tipo del vehículo.
ESTADOS_QUE_DEPENDEN_DEL_TIPO = (Estado.PENDIENTE, Estado.EN_PROCESO)

MENSAJE_CAMBIO_DE_TIPO = (
    'No se puede cambiar el tipo de un vehículo con turnos pendientes o en proceso.'
)


def tiene_turnos_en_curso(vehiculo):
    return vehiculo.turnos.filter(estado__in=ESTADOS_QUE_DEPENDEN_DEL_TIPO).exists()


def puede_cambiar_de_tipo(vehiculo, nuevo_tipo):
    """El tipo solo se puede cambiar si no hay turnos que dependan de él."""
    return nuevo_tipo == vehiculo.tipo or not tiene_turnos_en_curso(vehiculo)
