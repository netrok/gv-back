from django.db.models import Q
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.views import HealthBaseView
from .models import (
    Departamento, Puesto, Turno, Horario, Banco, Escolaridad, Estado, Municipio
)
from .serializers import (
    DepartamentoSerializer, PuestoSerializer, TurnoSerializer, HorarioSerializer,
    BancoSerializer, EscolaridadSerializer, EstadoSerializer, MunicipioSerializer
)


# /catalogos/health/
class HealthView(HealthBaseView):
    app_name = "catalogos"


# Permisos básicos: lectura para autenticados; escritura para staff/admin
class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class BaseCatalogoViewSet(viewsets.ModelViewSet):
    """
    - Búsqueda por ?search= (nombre/clave)
    - Filtro ?activo=true/false
    - Paginación estándar DRF
    """
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre", "clave", "descripcion"]
    filterset_fields = {"activo": ["exact"]}


class DepartamentoViewSet(BaseCatalogoViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer


class PuestoViewSet(BaseCatalogoViewSet):
    queryset = Puesto.objects.select_related("departamento").all()
    serializer_class = PuestoSerializer
    filterset_fields = {"activo": ["exact"], "departamento": ["exact"]}


class TurnoViewSet(BaseCatalogoViewSet):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer


class HorarioViewSet(BaseCatalogoViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer


class BancoViewSet(BaseCatalogoViewSet):
    queryset = Banco.objects.all()
    serializer_class = BancoSerializer


class EscolaridadViewSet(BaseCatalogoViewSet):
    queryset = Escolaridad.objects.all()
    serializer_class = EscolaridadSerializer


class EstadoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre", "abreviatura"]
    filterset_fields = {"activo": ["exact"]}


class MunicipioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Municipio.objects.select_related("estado").all()
    serializer_class = MunicipioSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre", "estado__nombre"]
    filterset_fields = {"activo": ["exact"], "estado": ["exact"]}

    @extend_schema(
        parameters=[
            OpenApiParameter(name="estado", description="ID de Estado", required=False, type=int),
            OpenApiParameter(name="search", description="Nombre de municipio", required=False, type=str),
            OpenApiParameter(name="activo", description="true/false", required=False, type=bool),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
