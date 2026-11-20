import re
from decimal import Decimal

from django.db import transaction
from django.db.models import Prefetch
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from catalogo.models import Box, Servicio, Tarifa, Vehiculo

# Formatos válidos: ABC123, AB123CD, 123ABC y A123BCD.
PATENTE_VALIDA = re.compile(
    r'^(?:[A-Z]{3}\d{3}|[A-Z]{2}\d{3}[A-Z]{2}|\d{3}[A-Z]{3}|[A-Z]\d{3}[A-Z]{3})$'
)

# Mensajes de los campos obligatorios de una tarifa.
CAMPOS_TARIFA = {
    'tipo_vehiculo': 'Elegí el tipo de vehículo.',
    'precio': 'Ingresá el precio.',
    'duracion_minutos': 'Ingresá la duración en minutos.',
}


def normalizar_patente(valor):
    """Mayúsculas, sin espacios ni guiones: 'ab-c 123' pasa a 'ABC123'."""
    return re.sub(r'[\s-]', '', valor).upper()


def servicios_con_tarifas():
    """Servicios con sus tarifas precargadas, ordenadas por id."""
    tarifas = Tarifa.objects.order_by('id')
    return Servicio.objects.prefetch_related(Prefetch('tarifas', queryset=tarifas))


class TarifaSerializer(serializers.ModelSerializer):
    precio = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        error_messages={
            'required': CAMPOS_TARIFA['precio'],
            'null': CAMPOS_TARIFA['precio'],
            'invalid': 'El precio no es válido.',
            'min_value': 'El precio tiene que ser mayor a 0.',
            'max_digits': 'El precio es demasiado grande.',
            'max_whole_digits': 'El precio es demasiado grande.',
            'max_decimal_places': 'El precio admite hasta 2 decimales.',
        },
    )
    duracion_minutos = serializers.IntegerField(
        min_value=1,
        max_value=2_147_483_647,
        error_messages={
            'required': CAMPOS_TARIFA['duracion_minutos'],
            'null': CAMPOS_TARIFA['duracion_minutos'],
            'invalid': 'La duración tiene que ser un número entero de minutos.',
            'min_value': 'La duración tiene que ser mayor a 0.',
            'max_value': 'La duración es demasiado grande.',
        },
    )

    class Meta:
        model = Tarifa
        fields = ['id', 'tipo_vehiculo', 'precio', 'duracion_minutos']
        extra_kwargs = {
            'tipo_vehiculo': {
                'error_messages': {
                    'required': CAMPOS_TARIFA['tipo_vehiculo'],
                    'null': CAMPOS_TARIFA['tipo_vehiculo'],
                    'invalid_choice': '"{input}" no es un tipo de vehículo válido.',
                },
            },
        }


class ServicioCatalogoSerializer(serializers.ModelSerializer):
    tarifas = TarifaSerializer(many=True, read_only=True)

    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'tarifas']


class ServicioSerializer(serializers.ModelSerializer):
    """Servicio con sus tarifas anidadas (alta, edición y consulta del administrador)."""

    tarifas = TarifaSerializer(many=True, required=False)

    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'activo', 'tarifas']
        extra_kwargs = {
            'nombre': {
                'error_messages': {
                    'required': 'Ingresá el nombre del servicio.',
                    'blank': 'Ingresá el nombre del servicio.',
                    'null': 'Ingresá el nombre del servicio.',
                    'max_length': 'El nombre admite hasta 100 caracteres.',
                },
            },
        }

    def validate_tarifas(self, tarifas):
        # En un PATCH, DRF omite los campos ausentes sin exigirlos: una tarifa
        # incompleta se rechaza acá, antes de tocar la base.
        errores = [
            {
                campo: [mensaje]
                for campo, mensaje in CAMPOS_TARIFA.items()
                if campo not in tarifa
            }
            for tarifa in tarifas
        ]
        if any(errores):
            raise serializers.ValidationError(errores)

        tipos = [tarifa['tipo_vehiculo'] for tarifa in tarifas]
        if len(tipos) != len(set(tipos)):
            raise serializers.ValidationError(
                'No se puede repetir el tipo de vehículo en las tarifas.'
            )
        return tarifas

    def create(self, validated_data):
        tarifas = validated_data.pop('tarifas', [])
        with transaction.atomic():
            servicio = Servicio.objects.create(**validated_data)
            self._guardar_tarifas(servicio, tarifas)
        return servicios_con_tarifas().get(pk=servicio.pk)

    def update(self, instance, validated_data):
        tarifas = validated_data.pop('tarifas', [])
        with transaction.atomic():
            for campo, valor in validated_data.items():
                setattr(instance, campo, valor)
            instance.save()
            self._guardar_tarifas(instance, tarifas)
        return servicios_con_tarifas().get(pk=instance.pk)

    @staticmethod
    def _guardar_tarifas(servicio, tarifas):
        """Crea o actualiza la tarifa de cada tipo enviado; los demás quedan como están."""
        for datos in tarifas:
            Tarifa.objects.update_or_create(
                servicio=servicio,
                tipo_vehiculo=datos['tipo_vehiculo'],
                defaults={
                    'precio': datos['precio'],
                    'duracion_minutos': datos['duracion_minutos'],
                },
            )


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = ['id', 'nombre', 'activo']
        extra_kwargs = {
            'nombre': {
                'validators': [
                    UniqueValidator(
                        queryset=Box.objects.all(),
                        message='Ya existe un box con ese nombre.',
                    )
                ],
                'error_messages': {
                    'required': 'Ingresá el nombre del box.',
                    'blank': 'Ingresá el nombre del box.',
                    'null': 'Ingresá el nombre del box.',
                    'max_length': 'El nombre admite hasta 50 caracteres.',
                },
            },
        }


class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = ['id', 'patente', 'tipo', 'activo']
        read_only_fields = ['activo']
        extra_kwargs = {
            # Se quita el validador de unicidad automático: validaría la patente
            # sin normalizar. La unicidad se controla en validate_patente.
            'patente': {
                'validators': [],
                'error_messages': {
                    'required': 'Ingresá la patente.',
                    'blank': 'Ingresá la patente.',
                    'null': 'Ingresá la patente.',
                },
            },
            'tipo': {
                'error_messages': {
                    'required': 'Elegí el tipo de vehículo.',
                    'null': 'Elegí el tipo de vehículo.',
                    'invalid_choice': '"{input}" no es un tipo de vehículo válido.',
                },
            },
        }

    def validate_patente(self, valor):
        patente = normalizar_patente(valor)
        if not PATENTE_VALIDA.match(patente):
            raise serializers.ValidationError(
                'La patente no tiene un formato válido (por ejemplo, ABC123 o AB123CD).'
            )
        repetidas = Vehiculo.objects.filter(patente=patente)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError('Ya hay un vehículo registrado con esa patente.')
        return patente
