"""Estados de un turno y el flujo que pueden seguir."""

from django.db import models


class Estado(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    EN_PROCESO = 'en_proceso', 'En proceso'
    FINALIZADO = 'finalizado', 'Finalizado'
    ENTREGADO = 'entregado', 'Entregado'
    CANCELADO = 'cancelado', 'Cancelado'


# Cada estado y el único estado al que se puede avanzar desde él.
# `entregado` y `cancelado` son finales: no tienen siguiente.
SIGUIENTE_ESTADO = {
    Estado.PENDIENTE: Estado.EN_PROCESO,
    Estado.EN_PROCESO: Estado.FINALIZADO,
    Estado.FINALIZADO: Estado.ENTREGADO,
}

# Estados en los que el turno ocupa un box. Un turno cancelado libera su horario.
ESTADOS_QUE_OCUPAN_BOX = (
    Estado.PENDIENTE,
    Estado.EN_PROCESO,
    Estado.FINALIZADO,
    Estado.ENTREGADO,
)