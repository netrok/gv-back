from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthView, EmpleadoViewSet

router = DefaultRouter()
router.register(r"", EmpleadoViewSet, basename="empleado")

urlpatterns = [
    path("health/", HealthView.as_view(), name="empleados-health"),
    path("", include(router.urls)),
]
