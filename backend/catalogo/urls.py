from django.urls import path
from rest_framework.routers import SimpleRouter

from catalogo.views import CatalogoView, VehiculoViewSet

router = SimpleRouter()
router.register('vehiculos', VehiculoViewSet, basename='vehiculo')

urlpatterns = [
    path('catalogo/', CatalogoView.as_view(), name='catalogo'),
    *router.urls,
]
