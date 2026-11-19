import re

from rest_framework import serializers

from catalogo.models import Servicio, Tarifa, Vehiculo

# Formatos válidos: ABC123, AB123CD, 123ABC y A123BCD.
PATENTE_VALIDA = re.compile(
    r'^(?:[A-Z]{3}\d{3}|[A-Z]{2}\d{3}[A-Z]{2}|\d{3}[A-Z]{3}|[A-Z]\d{3}[A-Z]{3})$'
)


def normalizar_patente(valor):
    """Mayúsculas, sin espacios ni guiones: 'ab-c 123' pasa a 'ABC123'."""
    return re.sub(r'[\s-]', '', valor).upper()


class TarifaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarifa
        fields = ['id', 'tipo_vehiculo', 'precio', 'duracion_minutos']


class ServicioCatalogoSerializer(serializers.ModelSerializer):
    tarifas = TarifaSerializer(many=True, read_only=True)

    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'tarifas']


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
