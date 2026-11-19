from rest_framework import serializers

from catalogo.models import Servicio, Tarifa


class TarifaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarifa
        fields = ['id', 'tipo_vehiculo', 'precio', 'duracion_minutos']


class ServicioCatalogoSerializer(serializers.ModelSerializer):
    tarifas = TarifaSerializer(many=True, read_only=True)

    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'tarifas']
