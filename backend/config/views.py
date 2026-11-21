from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    summary='Estado del servicio',
    description='Indica que el backend está funcionando. No requiere autenticación.',
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='EstadoServicio',
                fields={'status': serializers.CharField()},
            ),
            description='El servicio está activo.',
        )
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'status': 'ok'})