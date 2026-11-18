from rest_framework.routers import SimpleRouter

from turnos.views import TurnoViewSet

router = SimpleRouter()
router.register('turnos', TurnoViewSet, basename='turno')

urlpatterns = router.urls