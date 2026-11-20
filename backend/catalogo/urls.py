from django.urls import path
from rest_framework.routers import SimpleRouter

from catalogo.views import BoxViewSet, CatalogoView, ServicioViewSet, VehiculoViewSet

router = SimpleRouter()
router.register('servicios', ServicioViewSet, basename='servicio')
router.register('boxes', BoxViewSet, basename='box')
router.register('vehiculos', VehiculoViewSet, basename='vehiculo')

urlpatterns = [
    path('catalogo/', CatalogoView.as_view(), name='catalogo'),
    *router.urls,
]
