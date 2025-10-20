# backend/vacaciones/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # importamos el módulo completo para registrar condicionalmente

router = DefaultRouter()

def _register(viewset_attr: str, prefix: str, basename: str):
    """Registra el ViewSet si está definido en .views."""
    vs = getattr(views, viewset_attr, None)
    if vs is not None:
        router.register(prefix, vs, basename=basename)

# Rutas “clásicas”
_register("PoliticaViewSet",   "politicas",   "vac-politica")
_register("FeriadoViewSet",    "feriados",    "vac-feriado")
_register("BalanceViewSet",    "balances",    "vac-balance")
_register("SolicitudViewSet",  "solicitudes", "vac-solicitud")

# Nuevo ViewSet de solicitudes de vacaciones
_register("SolicitudVacacionesViewSet", "vacaciones", "vacaciones")

urlpatterns = [
    path("", include(router.urls)),
]

# Endpoint admin-only para reconstruir balances (si existe)
if hasattr(views, "RebuildBalancesView"):
    urlpatterns.append(
        path("balances/rebuild/", views.RebuildBalancesView.as_view(), name="vac-balances-rebuild")
    )
