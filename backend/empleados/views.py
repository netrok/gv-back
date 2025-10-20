from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.views import HealthBaseView
from .models import Empleado
from .serializers import EmpleadoSerializer, EmpleadoFotoSerializer


# /empleados/health/
class HealthView(HealthBaseView):
    app_name = "empleados"


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class EmpleadoViewSet(viewsets.ModelViewSet):
    """
    CRUD de Empleado con:
    - búsqueda: ?search= (nombre, número, RFC, CURP, NSS, email)
    - filtros: estatus, sucursal, area, departamento, puesto, unidad_negocio
    - paginación DRF estándar
    - restricción: usuario NO staff solo ve su propio expediente (si está ligado)
    """
    permission_classes = [IsStaffOrReadOnly]
    queryset = Empleado.objects.select_related(
        "banco", "escolaridad",
        "domicilio_estado", "domicilio_municipio",
        "nacimiento_estado", "nacimiento_municipio",
        "unidad_negocio", "sucursal", "area", "departamento",
        "puesto", "turno", "horario", "supervisor", "usuario",
    ).all()
    serializer_class = EmpleadoSerializer

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = [
        "numero_empleado", "primer_nombre", "segundo_nombre", "apellido_paterno", "apellido_materno",
        "rfc", "curp", "nss", "email_personal", "email_corporativo",
    ]
    filterset_fields = {
        "estatus": ["exact"],
        "unidad_negocio": ["exact"],
        "sucursal": ["exact"],
        "area": ["exact"],
        "departamento": ["exact"],
        "puesto": ["exact"],
        "turno": ["exact"],
        "horario": ["exact"],
        "sexo": ["exact"],
        "banco": ["exact"],
        "escolaridad": ["exact"],
    }

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        # Usuario normal autenticado (no staff): solo su propio registro (si está ligado)
        if u.is_authenticated and not u.is_staff:
            return qs.filter(usuario=u)
        return qs

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user, actualizado_por=self.request.user)

    def perform_update(self, serializer):
        serializer.save(actualizado_por=self.request.user)

    @extend_schema(
        methods=["GET"],
        parameters=[
            OpenApiParameter(name="search", description="Nombre/RFC/CURP/NSS/No. empleado", required=False, type=str),
            OpenApiParameter(name="estatus", description="A/B/S/L", required=False, type=str),
            OpenApiParameter(name="sucursal", description="ID sucursal", required=False, type=int),
            OpenApiParameter(name="departamento", description="ID departamento", required=False, type=int),
            OpenApiParameter(name="puesto", description="ID puesto", required=False, type=int),
        ],
        tags=["empleados"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    # /empleados/{id}/foto/ (POST: multipart)
    @extend_schema(request=EmpleadoFotoSerializer, responses=EmpleadoFotoSerializer, tags=["empleados"])
    @action(detail=True, methods=["post"], url_path="foto")
    def subir_foto(self, request, pk=None):
        empleado = self.get_object()
        serializer = EmpleadoFotoSerializer(empleado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
