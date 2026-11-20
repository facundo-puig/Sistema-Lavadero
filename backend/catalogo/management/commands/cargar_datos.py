from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogo.models import Box, Servicio, Tarifa, TipoVehiculo, Vehiculo

Usuario = get_user_model()

CONTRASENA = 'Lavadero123!'

BOXES = ['Box 1', 'Box 2']

# Cada servicio trae su tarifa (precio, minutos) por tipo de vehículo.
# "Aspirado interior" no tiene tarifa para moto, a propósito: sirve para probar el 400.
SERVICIOS = [
    {
        'nombre': 'Lavado exterior',
        'descripcion': 'Carrocería, llantas y vidrios.',
        'tarifas': {
            TipoVehiculo.AUTO: ('6000.00', 30),
            TipoVehiculo.CAMIONETA: ('8000.00', 40),
            TipoVehiculo.MOTO: ('3500.00', 20),
        },
    },
    {
        'nombre': 'Lavado completo',
        'descripcion': 'Exterior, interior y aspirado.',
        'tarifas': {
            TipoVehiculo.AUTO: ('12500.00', 45),
            TipoVehiculo.CAMIONETA: ('16000.00', 60),
            TipoVehiculo.MOTO: ('6000.00', 25),
        },
    },
    {
        'nombre': 'Encerado',
        'descripcion': 'Cera protectora y brillo.',
        'tarifas': {
            TipoVehiculo.AUTO: ('9000.00', 40),
            TipoVehiculo.CAMIONETA: ('12000.00', 50),
            TipoVehiculo.MOTO: ('5000.00', 30),
        },
    },
    {
        'nombre': 'Aspirado interior',
        'descripcion': 'Aspirado de butacas, alfombras y baúl.',
        'tarifas': {
            TipoVehiculo.AUTO: ('4000.00', 20),
            TipoVehiculo.CAMIONETA: ('5500.00', 25),
        },
    },
]

USUARIOS = [
    ('admin@lavadero.test', 'Admin', 'Lavadero', Usuario.Rol.ADMINISTRADOR),
    ('operario@lavadero.test', 'Omar', 'Operario', Usuario.Rol.OPERARIO),
    ('cliente@lavadero.test', 'Ana', 'Gómez', Usuario.Rol.CLIENTE),
]


class Command(BaseCommand):
    help = (
        'Carga datos de ejemplo: boxes, servicios con tarifas, un administrador, '
        'un operario y un cliente con un vehículo. Se puede correr varias veces.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Permite correrlo con DEBUG=False (por ejemplo, en una demo desplegada).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options['forzar']:
            raise CommandError(
                'Este comando crea usuarios con contraseñas conocidas. Con DEBUG=False '
                'solo corre con --forzar.'
            )

        for nombre in BOXES:
            Box.objects.get_or_create(nombre=nombre)

        for datos in SERVICIOS:
            servicio, _ = Servicio.objects.get_or_create(
                nombre=datos['nombre'],
                defaults={'descripcion': datos['descripcion']},
            )
            for tipo, (precio, minutos) in datos['tarifas'].items():
                Tarifa.objects.update_or_create(
                    servicio=servicio,
                    tipo_vehiculo=tipo,
                    defaults={'precio': precio, 'duracion_minutos': minutos},
                )

        por_rol = {}
        for email, nombre, apellido, rol in USUARIOS:
            usuario, creado = Usuario.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': nombre,
                    'last_name': apellido,
                    'rol': rol,
                },
            )
            if creado:
                usuario.set_password(CONTRASENA)
                usuario.save(update_fields=['password'])
            por_rol[rol] = usuario

        Vehiculo.objects.get_or_create(
            patente='AB123CD',
            defaults={
                'cliente': por_rol[Usuario.Rol.CLIENTE],
                'tipo': TipoVehiculo.AUTO,
            },
        )

        self.stdout.write(self.style.SUCCESS('Datos de ejemplo cargados.'))
        for email, _, _, rol in USUARIOS:
            self.stdout.write(f'  {rol:<14} {email}  /  {CONTRASENA}')
