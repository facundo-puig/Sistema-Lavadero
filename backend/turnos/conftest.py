"""Fixtures compartidos de los tests de turnos: cliente, vehículo, boxes, servicio y un
creador de turnos. Pytest los carga solo; el test los usa nombrándolos como parámetro."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from catalogo.models import Box, Servicio, TipoVehiculo, Vehiculo
from turnos.estados import Estado
from turnos.models import Turno

Usuario = get_user_model()


@pytest.fixture
def cliente(db):
    return Usuario.objects.create_user(
        username='ana@test.com', email='ana@test.com', password='Test12345!'
    )


@pytest.fixture
def vehiculo(cliente):
    return Vehiculo.objects.create(cliente=cliente, patente='AB123CD', tipo=TipoVehiculo.AUTO)


@pytest.fixture
def box_1(db):
    return Box.objects.create(nombre='Box 1')


@pytest.fixture
def box_2(db):
    return Box.objects.create(nombre='Box 2')


@pytest.fixture
def servicio(db):
    return Servicio.objects.create(nombre='Lavado exterior')


@pytest.fixture
def crear_turno(vehiculo, box_1):
    """Crea un turno directamente en la base. Por defecto: box 1, de 13:00 a 14:00 UTC."""

    def _crear(inicio=None, fin=None, box=None, estado=Estado.PENDIENTE):
        return Turno.objects.create(
            vehiculo=vehiculo,
            box=box or box_1,
            inicio=inicio or datetime(2026, 11, 20, 13, 0, tzinfo=UTC),
            fin=fin or datetime(2026, 11, 20, 14, 0, tzinfo=UTC),
            estado=estado,
            precio_total=Decimal('6000.00'),
        )

    return _crear