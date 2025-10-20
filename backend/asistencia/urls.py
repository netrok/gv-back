from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthView, ChecadaViewSet, JustificacionViewSet, ResumenAsistenciaView

router = DefaultRouter()
router.register(r"checks", ChecadaViewSet, basename="checada")
router.register(r"justificaciones", JustificacionViewSet, basename="justificacion")

urlpatterns = [
    path("health/", HealthView.as_view(), name="asistencia-health"),
    path("resumen/", ResumenAsistenciaView.as_view(), name="asistencia-resumen"),
    path("", include(router.urls)),
]
