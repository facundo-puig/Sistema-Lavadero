from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from turnos.filtros import TurnoFilter
from turnos.models import Turno, TurnoServicio
from turnos.reservas import reservar_turno
from turnos.serializers import ReservaSerializer, TurnoAgendaSerializer, TurnoSerializer
from turnos.services import ErrorDeTurno, validar_cancelacion
from usuarios.permisos import EsCliente

Usuario = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary='Listar turnos',
        description=(
            'El cliente ve solo sus turnos. Administrador y operario ven todos, con el cliente '
            'incluido (es la agenda). Ordenados por inicio, paginados de a 20. Filtros '
            'opcionales: `fecha` (día en hora de Argentina), `box` (id) y `estado`; un valor '
            'inválido devuelve 400.'
        ),
    ),
    retrieve=extend_schema(
        summary='Detalle de un turno',
        description='Devuelve 404 si el turno no existe o es de otro cliente.',
    ),
)
class TurnoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TurnoSerializer
    queryset = Turno.objects.all()
    filterset_class = TurnoFilter

    def get_permissions(self):
        # Reservar es solo para clientes. Listar, ver el detalle y cancelar los usan los tres
        # roles; el queryset ya limita al cliente a sus propios turnos.
        if self.action == 'create':
            return [EsCliente()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        # El personal ve además el cliente de cada turno (es la base de la agenda).
        rol = getattr(self.request.user, 'rol', None)
        if self.action in ('list', 'retrieve') and rol in (
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.OPERARIO,
        ):
            return TurnoAgendaSerializer
        return TurnoSerializer

    def get_permissions(self):
        # Reservar es solo para clientes. Listar, ver el detalle y cancelar los usan los tres
        # roles; el queryset ya limita al cliente a sus propios turnos.
        if self.action == 'create':
            return [EsCliente()]
        return [IsAuthenticated()]

    def get_queryset(self):
        turnos = Turno.objects.select_related('vehiculo__cliente', 'box').prefetch_related(
            Prefetch('servicios', queryset=TurnoServicio.objects.select_related('servicio'))
        )
        usuario = self.request.user
        if usuario.rol == Usuario.Rol.CLIENTE:
            # Un cliente nunca ve (ni sabe que existe) un turno de otro: da 404.
            return turnos.filter(vehiculo__cliente=usuario)
        return turnos

    @extend_schema(
        summary='Reservar un turno',
        description=(
            'El cliente elige vehículo, servicios y horario de inicio. El backend calcula el '
            'precio total y la hora de fin, y asigna el primer box libre. '
            'Devuelve 409 si no hay ningún box libre en ese horario.'
        ),
        request=ReservaSerializer,
        responses={201: TurnoSerializer},
    )
    def create(self, request):
        entrada = ReservaSerializer(data=request.data, context={'request': request})
        entrada.is_valid(raise_exception=True)

        try:
            turno = reservar_turno(**entrada.validated_data)
        except ErrorDeTurno as error:
            return Response(error.detalle, status=error.codigo_http)

        turno = self.get_queryset().get(pk=turno.pk)
        return Response(TurnoSerializer(turno).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary='Cancelar un turno',
        description=(
            'Cancela un turno pendiente y libera el horario. El cliente solo puede cancelar '
            'sus turnos (los ajenos dan 404). Devuelve 400 si el turno no está pendiente.'
        ),
        request=None,
        responses={200: TurnoSerializer},
    )
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        turno = self.get_object()  # 404 si no existe o es de otro cliente

        with transaction.atomic():
            # Se bloquea la fila para que dos pedidos a la vez no cancelen dos veces.
            turno_actual = Turno.objects.select_for_update().get(pk=turno.pk)
            try:
                turno_actual.estado = validar_cancelacion(turno_actual.estado)
            except ErrorDeTurno as error:
                return Response(error.detalle, status=error.codigo_http)
            turno_actual.save(update_fields=['estado'])

        turno = self.get_queryset().get(pk=turno.pk)
        return Response(TurnoSerializer(turno).data)