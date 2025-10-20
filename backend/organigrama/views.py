# backend/organigrama/views.py
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.views import HealthBaseView
from .models import UnidadNegocio, Sucursal, Area, Ubicacion
from .serializers import (
    UnidadNegocioSerializer, SucursalSerializer, AreaSerializer, UbicacionSerializer
)


# /organigrama/health/
@extend_schema(tags=["health"])
class HealthView(HealthBaseView):
    app_name = "organigrama"


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


@extend_schema(tags=["organigrama"])
@extend_schema(tags=["organigrama"])
class UnidadNegocioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = UnidadNegocio.objects.all()
    serializer_class = UnidadNegocioSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["nombre", "clave", "descripcion"]
    filterset_fields = {"activo": ["exact"]}
    ordering_fields = ["nombre", "id", "activo"]
    ordering = ["nombre"]


@extend_schema(tags=["organigrama"])
@extend_schema(tags=["organigrama"])
class SucursalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Sucursal.objects.select_related("unidad").all()
    serializer_class = SucursalSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["nombre", "clave", "ciudad", "estado", "descripcion", "unidad__nombre"]
    filterset_fields = {"activo": ["exact"], "unidad": ["exact"]}
    ordering_fields = ["nombre", "id", "activo", "unidad"]
    ordering = ["nombre"]


@extend_schema(tags=["organigrama"])
@extend_schema(tags=["organigrama"])
class AreaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Area.objects.select_related("sucursal", "parent").all()
    serializer_class = AreaSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["nombre", "clave", "descripcion", "sucursal__nombre", "parent__nombre"]
    filterset_fields = {
        "activo": ["exact"],
        "sucursal": ["exact"],
        "parent": ["exact"],
    }
    ordering_fields = ["nombre", "id", "activo", "sucursal", "parent"]
    ordering = ["nombre"]


@extend_schema(tags=["organigrama"])
@extend_schema(tags=["organigrama"])
class UbicacionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Ubicacion.objects.select_related("sucursal", "area").all()
    serializer_class = UbicacionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["nombre", "sucursal__nombre", "area__nombre"]
    filterset_fields = {"activo": ["exact"], "sucursal": ["exact"], "area": ["exact"]}
    ordering_fields = ["nombre", "id", "activo", "sucursal", "area"]
    ordering = ["nombre"]

    @extend_schema(
        tags=["organigrama"],
        parameters=[
            OpenApiParameter(name="sucursal", description="ID de sucursal", required=False, type=int),
            OpenApiParameter(name="area", description="ID de Ã¡rea", required=False, type=int),
            OpenApiParameter(name="search", description="Nombre de ubicaciÃ³n", required=False, type=str),
            OpenApiParameter(name="activo", description="true/false", required=False, type=bool),
            OpenApiParameter(name="ordering", description="nombre|id|activo|sucursal|area (usa - para descendente)", required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

