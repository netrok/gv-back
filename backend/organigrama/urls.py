from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthView, UnidadNegocioViewSet, SucursalViewSet, AreaViewSet, UbicacionViewSet

router = DefaultRouter()
router.register(r"unidades", UnidadNegocioViewSet, basename="unidad-negocio")
router.register(r"sucursales", SucursalViewSet, basename="sucursal")
router.register(r"areas", AreaViewSet, basename="area")
router.register(r"ubicaciones", UbicacionViewSet, basename="ubicacion")

urlpatterns = [
    path("health/", HealthView.as_view(), name="organigrama-health"),
    path("", include(router.urls)),
]
