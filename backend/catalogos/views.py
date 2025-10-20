# backend/catalogos/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.filters import OrderingFilter, SearchFilter
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
@extend_schema(tags=["health"])
class HealthView(HealthBaseView):
    app_name = "catalogos"


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


@extend_schema(tags=["catalogos"])


class BaseCatalogoViewSet(viewsets.ModelViewSet):
    """
    - BÃºsqueda por ?search= (nombre/clave/descripcion)
    - Filtro ?activo=true/false
    - Ordenamiento por ?ordering=nombre|id|activo (prefijo '-' para desc)
    - PaginaciÃ³n estÃ¡ndar DRF
    """
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["nombre", "clave", "descripcion"]
    filterset_fields = {"activo": ["exact"]}
    ordering_fields = ["nombre", "id", "activo"]
    ordering = ["nombre"]


@extend_schema(tags=["catalogos"])
@extend_schema(tags=["catalogos"])
class DepartamentoViewSet(BaseCatalogoViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer


@extend_schema(tags=["catalogos"])
@extend_schema(tags=["catalogos"])
class PuestoViewSet(BaseCatalogoViewSet):
    queryset = Puesto.objects.select_related("departamento").all()
    serializer_class = PuestoSerializer
    filterset_fields = {"activo": ["exact"], "departamento": ["exact"]}


@extend_schema(tags=["catalogos"])
@extend_schema(tags=["catalogos"])
class TurnoViewSet(BaseCatalogoViewSet):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer


@extend_schema(tags=["catalogos"])
@extend_schema(tags=["catalogos"])
class HorarioViewSet(BaseCatalogoViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer


@extend_schema(tags=["catalogos"])
@extend_schema(tags=["catalogos"])
class BancoViewSet(BaseCatalogoViewSet):
    queryset = Banco.objects.all()
    serializer_class = BancoSerializer


@extend_schema(tags=["catalogos"])
@extend_schema(tags=["catalogos"])
class EscolaridadViewSet(BaseCatalogoViewSet):
    queryset = Escolaridad.objects.all()
    serializer_class = EscolaridadSerializer


@extend_schema(tags=["catalogos"])
@extend_schema(tags=["catalogos"])
class EstadoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["nombre", "abreviatura"]
    filterset_fields = {"activo": ["exact"]}
    ordering_fields = ["nombre", "id", "activo"]
    ordering = ["nombre"]


@extend_schema(tags=["catalogos"])
@extend_schema(tags=["catalogos"])
class MunicipioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Municipio.objects.select_related("estado").all()
    serializer_class = MunicipioSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["nombre", "estado__nombre"]
    filterset_fields = {"activo": ["exact"], "estado": ["exact"]}
    ordering_fields = ["nombre", "id", "activo"]
    ordering = ["nombre"]

    @extend_schema(
        tags=["catalogos"],
        parameters=[
            OpenApiParameter(name="estado", description="ID de Estado", required=False, type=int),
            OpenApiParameter(name="search", description="Nombre de municipio", required=False, type=str),
            OpenApiParameter(name="activo", description="true/false", required=False, type=bool),
            OpenApiParameter(name="ordering", description="nombre|id|activo (usar - para descendente)", required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

