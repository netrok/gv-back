from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    HealthView, DepartamentoViewSet, PuestoViewSet, TurnoViewSet, HorarioViewSet,
    BancoViewSet, EscolaridadViewSet, EstadoViewSet, MunicipioViewSet
)

router = DefaultRouter()
router.register(r"departamentos", DepartamentoViewSet, basename="departamento")
router.register(r"puestos", PuestoViewSet, basename="puesto")
router.register(r"turnos", TurnoViewSet, basename="turno")
router.register(r"horarios", HorarioViewSet, basename="horario")
router.register(r"bancos", BancoViewSet, basename="banco")
router.register(r"escolaridades", EscolaridadViewSet, basename="escolaridad")
router.register(r"estados", EstadoViewSet, basename="estado")
router.register(r"municipios", MunicipioViewSet, basename="municipio")

urlpatterns = [
    path("health/", HealthView.as_view(), name="catalogos-health"),
    path("", include(router.urls)),
]
