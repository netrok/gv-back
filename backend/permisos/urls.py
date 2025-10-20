from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TipoPermisoViewSet, PermisoViewSet

router = DefaultRouter()
router.register(r"tipos", TipoPermisoViewSet, basename="permiso-tipo")
router.register(r"", PermisoViewSet, basename="permiso")

urlpatterns = [ path("", include(router.urls)), ]
