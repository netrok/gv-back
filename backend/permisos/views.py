from django.utils import timezone
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import TipoPermiso, Permiso
from .serializers import TipoPermisoSerializer, PermisoSerializer

class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET","HEAD","OPTIONS"):
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff

class TipoPermisoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = TipoPermiso.objects.filter(activo=True)
    serializer_class = TipoPermisoSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre"]
    filterset_fields = {"con_goce":["exact"], "requiere_evidencia":["exact"], "activo":["exact"]}

class PermisoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Permiso.objects.select_related("empleado","tipo","aprobado_por").all()
    serializer_class = PermisoSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["empleado__primer_nombre","empleado__apellido_paterno","motivo","tipo__nombre"]
    filterset_fields = {"empleado":["exact"],"estado":["exact"],"fecha_inicio":["gte","lte"],"fecha_fin":["gte","lte"],"tipo":["exact"]}

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.is_staff:
            return qs
        if hasattr(u, "empleado"):
            return qs.filter(empleado=u.empleado)
        return qs.none()

    def perform_create(self, serializer):
        u = self.request.user
        # no-staff solo puede crear para sí mismo
        emp = serializer.validated_data.get("empleado")
        if not u.is_staff:
            if not hasattr(u, "empleado") or emp != u.empleado:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No puedes crear permisos para otro empleado.")
        serializer.save(creado_por=u)

    @action(detail=True, methods=["post"], url_path="aprobar", permission_classes=[permissions.IsAdminUser])
    def aprobar(self, request, pk=None):
        p = self.get_object()
        if p.estado != "PEND":
            return Response({"detail":"Solo PEND pueden aprobarse."}, status=400)
        p.estado = "APROB"; p.aprobado_por = request.user; p.aprobado_en = timezone.now()
        p.comentario_aprobador = request.data.get("comentario","")
        p.save(update_fields=["estado","aprobado_por","aprobado_en","comentario_aprobador"])
        return Response(self.get_serializer(p).data)

    @action(detail=True, methods=["post"], url_path="rechazar", permission_classes=[permissions.IsAdminUser])
    def rechazar(self, request, pk=None):
        p = self.get_object()
        if p.estado != "PEND":
            return Response({"detail":"Solo PEND pueden rechazarse."}, status=400)
        p.estado = "RECH"; p.aprobado_por = request.user; p.aprobado_en = timezone.now()
        p.comentario_aprobador = request.data.get("comentario","")
        p.save(update_fields=["estado","aprobado_por","aprobado_en","comentario_aprobador"])
        return Response(self.get_serializer(p).data)

    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        p = self.get_object()
        u = request.user
        if p.estado not in ("PEND","APROB"):
            return Response({"detail":"Solo PEND/APROB pueden cancelarse."}, status=400)
        if not u.is_staff and (not hasattr(u, "empleado") or p.empleado_id != u.empleado_id):
            return Response({"detail":"No puedes cancelar permisos de otro empleado."}, status=403)
        p.estado = "CANC"; p.save(update_fields=["estado"])
        return Response(self.get_serializer(p).data)
