from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from core.views import HealthBaseView
from .models import Checada, Justificacion
from .serializers import ChecadaSerializer, JustificacionSerializer


# ========= Helpers =========
def _has_field(model, name: str) -> bool:
    return any(getattr(f, "name", None) == name for f in model._meta.get_fields())


# ========= Health =========
@extend_schema(tags=["health"])
class HealthView(HealthBaseView):
    app_name = "asistencia"


# ========= Permisos base =========
class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


# ========= Checadas =========
@extend_schema(tags=["asistencia"])
@extend_schema(tags=["asistencia"])
class ChecadaViewSet(viewsets.ModelViewSet):
    """
    CRUD de checadas con bÃºsqueda, filtros y ordenamiento.
    """
    permission_classes = [IsStaffOrReadOnly]
    queryset = Checada.objects.select_related("empleado").all()
    serializer_class = ChecadaSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        "empleado__primer_nombre",
        "empleado__apellido_paterno",
        "empleado__numero_empleado",
    ]
    ordering_fields = ["fecha", "hora", "id"]
    ordering = ["-fecha", "-id"]

    # âš ï¸ Definimos los filters dinÃ¡micamente como property para que DRF y Spectacular los tomen.
    @property
    def filterset_fields(self):
        fields = {
            "empleado": ["exact"],
            "fuente": ["exact"],  # core.enums.FuenteEnum si aplica
            "tipo": ["exact"],    # core.enums.TipoChecadaEnum si aplica
        }
        if _has_field(Checada, "fecha"):
            fields["fecha"] = ["exact", "gte", "lte"]
        else:
            if _has_field(Checada, "fecha_inicio"):
                fields["fecha_inicio"] = ["exact", "gte", "lte"]
            if _has_field(Checada, "fecha_fin"):
                fields["fecha_fin"] = ["exact", "gte", "lte"]
        return fields

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        examples=[OpenApiExample("OK", value={"detail": "Recalculado"})],
    )
    @action(detail=True, methods=["post"], url_path="recalcular", permission_classes=[permissions.IsAdminUser])
    def recalcular(self, request, pk=None):
        """
        AcciÃ³n administrativa para recalcular una checada (ej. reglas, redondeos, etc.).
        Implementa aquÃ­ tu lÃ³gica real si aplica.
        """
        _ = self.get_object()
        # TODO: lÃ³gica real de recÃ¡lculo
        return Response({"detail": "Recalculado"}, status=status.HTTP_200_OK)


# ========= Justificaciones =========
@extend_schema(tags=["asistencia"])
@extend_schema(tags=["asistencia"])
class JustificacionViewSet(viewsets.ModelViewSet):
    """
    Justificaciones de asistencia con flujo de resoluciÃ³n.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Justificacion.objects.select_related("empleado", "resuelto_por").all()
    serializer_class = JustificacionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["empleado__primer_nombre", "empleado__apellido_paterno", "motivo"]
    ordering_fields = ["fecha", "creado_en", "id"]
    ordering = ["-fecha", "-id"]

    @property
    def filterset_fields(self):
        fields = {
            "empleado": ["exact"],
            "estado": ["exact"],  # PEND/APROB/RECH
        }
        if _has_field(Justificacion, "fecha"):
            fields["fecha"] = ["exact", "gte", "lte"]
        else:
            if _has_field(Justificacion, "fecha_inicio"):
                fields["fecha_inicio"] = ["exact", "gte", "lte"]
            if _has_field(Justificacion, "fecha_fin"):
                fields["fecha_fin"] = ["exact", "gte", "lte"]
        return fields

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        examples=[OpenApiExample("OK", value={"detail": "Resuelta"})],
    )
    @action(detail=True, methods=["post"], url_path="resolver", permission_classes=[permissions.IsAdminUser])
    def resolver(self, request, pk=None):
        """
        Resuelve una justificaciÃ³n: body opcional {"aprobar": true, "comentario": "texto"}
        """
        j = self.get_object()
        approve = bool(request.data.get("aprobar", True))
        comentario = str(request.data.get("comentario", "") or "")
        if j.estado not in ("PEND",):
            return Response({"detail": "Solo PEND puede resolverse."}, status=status.HTTP_400_BAD_REQUEST)
        j.estado = "APROB" if approve else "RECH"
        if hasattr(j, "resuelto_por"):
            j.resuelto_por = request.user
        if hasattr(j, "resuelto_en"):
            j.resuelto_en = timezone.now()
        if hasattr(j, "comentario_resolucion"):
            j.comentario_resolucion = comentario
        j.save()
        return Response(self.get_serializer(j).data)


# ========= Resumen por dÃ­a =========
@extend_schema(
    tags=["asistencia"],
    parameters=[
        OpenApiParameter("fecha", str, description="YYYY-MM-DD (requerido)"),
        OpenApiParameter("empleado", int, description="ID empleado (opcional)"),
    ],
    examples=[OpenApiExample("Ejemplo", value={"fecha": "2025-01-31", "items": []})],
    responses={200: OpenApiTypes.OBJECT},  # documenta la respuesta y evita el warning
)
@extend_schema(tags=["asistencia"])
class ResumenAsistenciaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        s_fecha = request.query_params.get("fecha")
        if not s_fecha:
            return Response({"detail": "fecha es requerida (YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)
        d = parse_date(s_fecha)
        if not d:
            return Response({"detail": "Formato de fecha invÃ¡lido."}, status=status.HTTP_400_BAD_REQUEST)

        emp_id = request.query_params.get("empleado")
        qs = Checada.objects.select_related("empleado").filter(fecha=d)

        u = request.user
        if not u.is_staff:
            if hasattr(u, "empleado"):
                qs = qs.filter(empleado=u.empleado)
            else:
                qs = qs.none()

        if emp_id:
            qs = qs.filter(empleado_id=emp_id)

        data = []
        for c in qs:
            data.append({
                "empleado": {
                    "id": c.empleado_id,
                    "numero_empleado": getattr(c.empleado, "numero_empleado", None),
                    "nombre": getattr(c.empleado, "nombre_completo", None),
                },
                "fecha": f"{c.fecha:%Y-%m-%d}",
                "tipo": getattr(c, "tipo", None),
                "fuente": getattr(c, "fuente", None),
                "hora": getattr(c, "hora", None),
            })
        return Response({"fecha": f"{d:%Y-%m-%d}", "items": data})

