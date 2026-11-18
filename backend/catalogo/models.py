from django.conf import settings
from django.db import models


class TipoVehiculo(models.TextChoices):
    AUTO = "auto", "Auto"
    CAMIONETA = "camioneta", "Camioneta"
    MOTO = "moto", "Moto"


class Vehiculo(models.Model):
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehiculos",
    )
    patente = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=20, choices=TipoVehiculo.choices)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.patente


class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Tarifa(models.Model):
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name="tarifas",
    )
    tipo_vehiculo = models.CharField(max_length=20, choices=TipoVehiculo.choices)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["servicio", "tipo_vehiculo"],
                name="tarifa_unica_por_servicio_y_tipo",
            ),
            models.CheckConstraint(
                condition=models.Q(precio__gt=0),
                name="tarifa_precio_mayor_a_cero",
            ),
            models.CheckConstraint(
                condition=models.Q(duracion_minutos__gt=0),
                name="tarifa_duracion_mayor_a_cero",
            ),
        ]

    def __str__(self):
        return f"{self.servicio} - {self.tipo_vehiculo}"


class Box(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
