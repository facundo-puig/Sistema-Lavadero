from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from catalogo.models import Servicio, Tarifa, TipoVehiculo, Vehiculo

pytestmark = pytest.mark.django_db


@pytest.fixture
def cliente():
    Usuario = get_user_model()
    return Usuario.objects.create_user(
        username="ana@example.com",
        email="ana@example.com",
        password="clave-de-prueba-123",
    )


@pytest.fixture
def servicio():
    return Servicio.objects.create(nombre="Lavado completo")


def test_tarifa_unica_por_servicio_y_tipo_de_vehiculo(servicio):
    Tarifa.objects.create(
        servicio=servicio,
        tipo_vehiculo=TipoVehiculo.AUTO,
        precio=Decimal("9000.00"),
        duracion_minutos=45,
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Tarifa.objects.create(
                servicio=servicio,
                tipo_vehiculo=TipoVehiculo.AUTO,
                precio=Decimal("9500.00"),
                duracion_minutos=50,
            )


def test_mismo_servicio_admite_tarifas_de_distinto_tipo_de_vehiculo(servicio):
    Tarifa.objects.create(
        servicio=servicio,
        tipo_vehiculo=TipoVehiculo.AUTO,
        precio=Decimal("9000.00"),
        duracion_minutos=45,
    )
    Tarifa.objects.create(
        servicio=servicio,
        tipo_vehiculo=TipoVehiculo.MOTO,
        precio=Decimal("5000.00"),
        duracion_minutos=30,
    )
    assert servicio.tarifas.count() == 2


@pytest.mark.parametrize("precio", [Decimal("0.00"), Decimal("-1.00")])
def test_tarifa_con_precio_no_positivo_es_invalida(servicio, precio):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Tarifa.objects.create(
                servicio=servicio,
                tipo_vehiculo=TipoVehiculo.AUTO,
                precio=precio,
                duracion_minutos=45,
            )


def test_tarifa_con_duracion_cero_es_invalida(servicio):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Tarifa.objects.create(
                servicio=servicio,
                tipo_vehiculo=TipoVehiculo.AUTO,
                precio=Decimal("9000.00"),
                duracion_minutos=0,
            )


def test_patente_unica(cliente):
    Vehiculo.objects.create(cliente=cliente, patente="AB123CD", tipo=TipoVehiculo.AUTO)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Vehiculo.objects.create(
                cliente=cliente, patente="AB123CD", tipo=TipoVehiculo.MOTO
            )


def test_no_se_borra_un_cliente_con_vehiculos(cliente):
    Vehiculo.objects.create(cliente=cliente, patente="AB123CD", tipo=TipoVehiculo.AUTO)
    with pytest.raises(ProtectedError):
        cliente.delete()


def test_no_se_borra_un_servicio_con_tarifas(servicio):
    Tarifa.objects.create(
        servicio=servicio,
        tipo_vehiculo=TipoVehiculo.AUTO,
        precio=Decimal("9000.00"),
        duracion_minutos=45,
    )
    with pytest.raises(ProtectedError):
        servicio.delete()
