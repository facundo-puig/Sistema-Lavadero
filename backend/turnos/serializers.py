from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from catalogo.models import Box, Servicio, Vehiculo
from turnos.models import Turno, TurnoServicio


class ReservaSerializer(serializers.Serializer):
    """Entrada de `POST /api/turnos/`. El cliente no manda ni el fin, ni el precio, ni el box."""

    vehiculo = serializers.PrimaryKeyRelatedField(
        queryset=Vehiculo.objects.none(),
        error_messages={
            'required': 'Elegí un vehículo.',
            'null': 'Elegí un vehículo.',
            'does_not_exist': 'El vehículo no existe, no es tuyo o está inactivo.',
            'incorrect_type': 'Vehículo inválido.',
        },
    )
    servicios = serializers.PrimaryKeyRelatedField(
        many=True,
        allow_empty=False,
        queryset=Servicio.objects.filter(activo=True),
        error_messages={
            'required': 'Elegí al menos un servicio.',
            'null': 'Elegí al menos un servicio.',
            'empty': 'Elegí al menos un servicio.',
            'not_a_list': 'Los servicios tienen que ser una lista.',
            'does_not_exist': 'Uno de los servicios no existe o no está disponible.',
            'incorrect_type': 'Servicio inválido.',
        },
    )
    inicio = serializers.DateTimeField(
        error_messages={
            'required': 'Elegí la fecha y la hora de inicio.',
            'null': 'Elegí la fecha y la hora de inicio.',
            'invalid': 'Fecha inválida. Usá el formato 2026-11-20T13:00:00Z.',
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Al generar la documentación de Swagger el serializer se crea sin request.
        request = self.context.get('request')
        if request is not None:
            # Solo se puede reservar con un vehículo propio y activo.
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(
                cliente=request.user, activo=True
            )


class VehiculoResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = ['id', 'patente', 'tipo']


class BoxResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = ['id', 'nombre']


class ClienteResumenSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()


class TurnoServicioSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='servicio_id')
    nombre = serializers.CharField(source='servicio.nombre')
    precio_aplicado = serializers.DecimalField(source='precio', max_digits=10, decimal_places=2)

    class Meta:
        model = TurnoServicio
        fields = ['id', 'nombre', 'precio_aplicado']


class TurnoSerializer(serializers.ModelSerializer):
    """El objeto Turno de `docs/api-turnos.md`."""

    vehiculo = VehiculoResumenSerializer()
    box = BoxResumenSerializer()
    servicios = serializers.SerializerMethodField()

    class Meta:
        model = Turno
        fields = [
            'id',
            'vehiculo',
            'box',
            'inicio',
            'fin',
            'estado',
            'precio_total',
            'servicios',
        ]

    @extend_schema_field(TurnoServicioSerializer(many=True))
    def get_servicios(self, turno):
        # Orden estable: el de contratación. Usa los servicios ya precargados si los hay.
        items = sorted(turno.servicios.all(), key=lambda item: item.pk)
        return TurnoServicioSerializer(items, many=True).data

class TurnoAgendaSerializer(TurnoSerializer):
    """El Turno con el cliente incluido: lo que ven el administrador y el operario."""

    cliente = serializers.SerializerMethodField()

    class Meta(TurnoSerializer.Meta):
        fields = [*TurnoSerializer.Meta.fields, 'cliente']

    @extend_schema_field(ClienteResumenSerializer)
    def get_cliente(self, turno):
        cliente = turno.vehiculo.cliente
        return {'id': cliente.id, 'nombre': cliente.get_full_name() or cliente.email}