"""Tests de humo del backend base: health y paginación por defecto."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from rest_framework.test import APIClient, APIRequestFactory

Usuario = get_user_model()


def test_health_responde_ok_sin_sesion():
    respuesta = APIClient().get('/api/health/')

    assert respuesta.status_code == 200
    assert respuesta.json() == {'status': 'ok'}


class _UsuarioSerializer(ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'email']


class _ListadoDePrueba(ListAPIView):
    """Vista descartable: usa la paginación por defecto de DRF, sin configurarla."""

    permission_classes = [AllowAny]
    serializer_class = _UsuarioSerializer
    queryset = Usuario.objects.order_by('id')


@pytest.mark.django_db
def test_los_listados_se_paginan_de_a_20():
    for i in range(25):
        Usuario.objects.create_user(
            username=f'u{i}@test.com',
            email=f'u{i}@test.com',
            password='Test12345!',
        )

    pedido = APIRequestFactory().get('/listado/')
    datos = _ListadoDePrueba.as_view()(pedido).data

    assert datos['count'] == 25
    assert len(datos['results']) == 20
    assert datos['next'] is not None
    assert datos['previous'] is None