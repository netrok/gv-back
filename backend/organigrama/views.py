from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.views import HealthBaseView
from .models import UnidadNegocio, Sucursal, Area, Ubicacion
from .serializers import (
    UnidadNegocioSerializer, SucursalSerializer, AreaSerializer, UbicacionSerializer
)


# /organigrama/health/
class HealthView(HealthBaseView):
    app_name = "organigrama"


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class UnidadNegocioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = UnidadNegocio.objects.all()
    serializer_class = UnidadNegocioSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre", "clave", "descripcion"]
    filterset_fields = {"activo": ["exact"]}


class SucursalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Sucursal.objects.select_related("unidad").all()
    serializer_class = SucursalSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre", "clave", "ciudad", "estado", "descripcion"]
    filterset_fields = {"activo": ["exact"], "unidad": ["exact"]}


class AreaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Area.objects.select_related("sucursal", "parent").all()
    serializer_class = AreaSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre", "clave", "descripcion", "sucursal__nombre", "parent__nombre"]
    filterset_fields = {
        "activo": ["exact"],
        "sucursal": ["exact"],
        "parent": ["exact"],
    }


class UbicacionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Ubicacion.objects.select_related("sucursal", "area").all()
    serializer_class = UbicacionSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre", "sucursal__nombre", "area__nombre"]
    filterset_fields = {"activo": ["exact"], "sucursal": ["exact"], "area": ["exact"]}

    @extend_schema(
        parameters=[
            OpenApiParameter(name="sucursal", description="ID de sucursal", required=False, type=int),
            OpenApiParameter(name="area", description="ID de área", required=False, type=int),
            OpenApiParameter(name="search", description="Nombre de ubicación", required=False, type=str),
            OpenApiParameter(name="activo", description="true/false", required=False, type=bool),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
