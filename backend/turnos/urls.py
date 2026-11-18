from django.urls import path
from rest_framework.routers import SimpleRouter

from turnos.views import TurnoViewSet
from turnos.views_estado import CambiarEstadoView

router = SimpleRouter()
router.register('turnos', TurnoViewSet, basename='turno')

urlpatterns = [
    path('turnos/<int:pk>/estado/', CambiarEstadoView.as_view(), name='turno-estado'),
    *router.urls,
]