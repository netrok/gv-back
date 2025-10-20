from datetime import date
from decimal import Decimal

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter

from empleados.models import Empleado
from .models import (
    PoliticaVacaciones,
    Feriado,
    BalanceVacaciones,
    SolicitudVacaciones,   # usado por ambos bloques
)
from .serializers import (
    PoliticaVacacionesSerializer,
    FeriadoSerializer,
    BalanceVacacionesSerializer,
    SolicitudVacacionesSerializer,
    # Nuevo serializer de creaciÃ³n si lo tienes definido:
    # SolicitudVacacionesCreateSerializer,
)
from .utils import dias_habiles

# Si tienes serializer de creaciÃ³n separado, descomenta la import y esta bandera
HAS_CREATE_SERIALIZER = False  # pon True si existe SolicitudVacacionesCreateSerializer


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


# ======== POLÃTICAS ========
@extend_schema(tags=["vacaciones"])
@extend_schema(tags=["vacaciones"])
class PoliticaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = PoliticaVacaciones.objects.filter(activo=True)
    serializer_class = PoliticaVacacionesSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["dias"]  # texto sobre int; ok para bÃºsquedas simples
    filterset_fields = {
        "anios_desde": ["gte", "lte"],
        "anios_hasta": ["gte", "lte"],
        "activo": ["exact"],
    }


# ======== FERIADOS ========
@extend_schema(tags=["vacaciones"])
@extend_schema(tags=["vacaciones"])
class FeriadoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Feriado.objects.all()
    serializer_class = FeriadoSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nombre"]
    filterset_fields = {"fecha": ["exact", "gte", "lte"]}


# ======== BALANCES (solo lectura) ========
@extend_schema(tags=["vacaciones"])
@extend_schema(tags=["vacaciones"])
class BalanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = BalanceVacaciones.objects.select_related("empleado").all()
    serializer_class = BalanceVacacionesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {"empleado": ["exact"], "anio": ["exact"]}

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.is_staff:
            return qs
        if hasattr(u, "empleado"):
            return qs.filter(empleado=u.empleado)
        return qs.none()


# ======== SOLICITUDES (legacy) ========
@extend_schema(tags=["vacaciones"])
@extend_schema(tags=["vacaciones"])
class SolicitudViewSet(viewsets.ModelViewSet):
    """
    Vista histÃ³rica que opera sobre SolicitudVacaciones con campos
    como 'aprobado_por', 'aprobado_en', etc. Conservada por compatibilidad.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = SolicitudVacaciones.objects.select_related("empleado", "aprobado_por").all()
    serializer_class = SolicitudVacacionesSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = [
        "empleado__primer_nombre",
        "empleado__apellido_paterno",
        "empleado__numero_empleado",
        "motivo",
        "comentario",
    ]
    filterset_fields = {
        "empleado": ["exact"],
        "estado": ["exact"],
        "fecha_inicio": ["gte", "lte", "exact"],
        # âœ… corregido: lookups separados (no "gte, lte")
        "fecha_fin": ["gte", "lte", "exact"],
    }

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
        empleado = serializer.validated_data.get("empleado")
        # No staff: solo puede crear para sÃ­ mismo
        if not u.is_staff:
            if not hasattr(u, "empleado") or empleado != u.empleado:
                raise PermissionDenied("No puedes crear solicitudes para otro empleado.")
        serializer.save(creado_por=u)

    @extend_schema(
        methods=["get"], tags=["vacaciones"],
        parameters=[
            OpenApiParameter("fecha_inicio", str, description="YYYY-MM-DD", required=True),
            OpenApiParameter("fecha_fin", str, description="YYYY-MM-DD", required=True),
        ],
        description="Simula el cÃ¡lculo de dÃ­as hÃ¡biles (excluye fines de semana y feriados globales).",
    )
    @action(detail=False, methods=["get"], url_path="simular")
    def simular(self, request):
        fi = request.query_params.get("fecha_inicio")
        ff = request.query_params.get("fecha_fin")
        if not fi or not ff:
            return Response({"detail": "fecha_inicio y fecha_fin son requeridos"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            fi_d = date.fromisoformat(fi)
            ff_d = date.fromisoformat(ff)
        except Exception:
            return Response({"detail": "Formato de fecha invÃ¡lido"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"dias_habiles": dias_habiles(fi_d, ff_d)})

    @action(detail=True, methods=["post"], url_path="aprobar", permission_classes=[IsAdminUser])
    def aprobar(self, request, pk=None):
        s = self.get_object()
        if s.estado != "PEND":
            return Response({"detail": "Solo solicitudes PEND pueden aprobarse."}, status=status.HTTP_400_BAD_REQUEST)
        s.estado = "APROB"
        # Campos legacy:
        if hasattr(s, "aprobado_por"):
            s.aprobado_por = request.user
        if hasattr(s, "aprobado_en"):
            s.aprobado_en = timezone.now()
        if hasattr(s, "comentario_aprobador"):
            s.comentario_aprobador = request.data.get("comentario", "")
        s.save()
        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"], url_path="rechazar", permission_classes=[IsAdminUser])
    def rechazar(self, request, pk=None):
        s = self.get_object()
        if s.estado != "PEND":
            return Response({"detail": "Solo solicitudes PEND pueden rechazarse."}, status=status.HTTP_400_BAD_REQUEST)
        s.estado = "RECH"
        if hasattr(s, "aprobado_por"):
            s.aprobado_por = request.user
        if hasattr(s, "aprobado_en"):
            s.aprobado_en = timezone.now()
        if hasattr(s, "comentario_aprobador"):
            s.comentario_aprobador = request.data.get("comentario", "")
        s.save()
        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        s = self.get_object()
        u = request.user
        if s.estado not in ("PEND", "APROB"):
            return Response({"detail": "Solo PEND/APROB pueden cancelarse."}, status=status.HTTP_400_BAD_REQUEST)
        if not u.is_staff and (not hasattr(u, "empleado") or s.empleado_id != u.empleado_id):
            return Response({"detail": "No puedes cancelar solicitudes de otro empleado."}, status=status.HTTP_403_FORBIDDEN)
        s.estado = "CANC"
        s.save(update_fields=["estado"])
        return Response(self.get_serializer(s).data)


# ======== REBUILD BALANCES (admin-only) ========
def _antiguedad_anios(empleado, anio: int) -> int:
    base = empleado.fecha_antiguedad or empleado.fecha_alta
    if not base:
        return 0
    corte = date(anio, 1, 1)
    if base > corte:
        return 0
    return corte.year - base.year - ((corte.month, corte.day) < (base.month, base.day))


def _politica_para_anios(anios: int):
    return (
        PoliticaVacaciones.objects
        .filter(activo=True, anios_desde__lte=anios, anios_hasta__gte=anios)
        .order_by("anios_desde")
        .first()
    )


def _dias_tomados_en_anio(empleado_id: int, anio: int) -> Decimal:
    desde = date(anio, 1, 1)
    hasta = date(anio, 12, 31)
    qs = SolicitudVacaciones.objects.filter(
        empleado_id=empleado_id,
        estado="APROB",
        fecha_inicio__lte=hasta,
        fecha_fin__gte=desde,
    )
    total = Decimal("0.00")
    for s in qs:
        # Soporta modelado con 'dias' o 'dias_habiles'
        dias_val = getattr(s, "dias_habiles", None)
        if dias_val is None:
            dias_val = getattr(s, "dias", 0)
        total += Decimal(dias_val or 0)
    return total


@extend_schema(tags=["vacaciones"])


class RebuildBalancesView(APIView):
    """
    POST admin-only para recalcular balances.
    Body opcional: {"year": 2025, "solo_activos": true, "empleado": 1}
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["vacaciones"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "solo_activos": {"type": "boolean"},
                    "empleado": {"type": "integer"},
                },
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "procesados": {"type": "integer"},
                    "actualizados": {"type": "integer"},
                },
            }
        },
    )
    def post(self, request):
        anio = int(request.data.get("year") or date.today().year)
        solo_activos = bool(request.data.get("solo_activos") or False)
        empleado_id = request.data.get("empleado")

        qs = Empleado.objects.all()
        if solo_activos:
            qs = qs.filter(estatus="A")
        if empleado_id:
            qs = qs.filter(id=empleado_id)

        total = qs.count()
        actualizados = 0
        for emp in qs.iterator():
            anios = _antiguedad_anios(emp, anio)
            pol = _politica_para_anios(anios)
            dias_asignados = Decimal(getattr(pol, "dias", 0) if pol else 0)

            # Arrastre desde el aÃ±o previo, respetando arrastre_maximo si existe
            arrastre = Decimal("0.00")
            if pol:
                prev = BalanceVacaciones.objects.filter(empleado=emp, anio=anio - 1).first()
                if prev:
                    arr_max = Decimal(getattr(pol, "arrastre_maximo", 0) or 0)
                    arrastre = min(arr_max, max(Decimal("0.00"), prev.dias_disponibles))

            dias_tomados = _dias_tomados_en_anio(emp.id, anio)
            disp = dias_asignados + arrastre - dias_tomados
            if disp < 0:
                disp = Decimal("0.00")

            bal, _ = BalanceVacaciones.objects.get_or_create(empleado=emp, anio=anio)
            bal.dias_asignados = dias_asignados
            bal.dias_arrastrados = arrastre
            bal.dias_tomados = dias_tomados
            bal.dias_disponibles = disp
            bal.caduca_el = date(anio, 12, 31)
            bal.save()
            actualizados += 1

        return Response({"year": anio, "procesados": total, "actualizados": actualizados})


# ======== NUEVO: SolicitudVacacionesViewSet (v2) ========
# Usa mÃ©todos aprobar/rechazar/cancelar del modelo (si existen)
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.permissions import IsAuthenticatedReadOnlyOrRRHH, IsRRHHEditOnly

@extend_schema(tags=["vacaciones"])
@extend_schema(tags=["vacaciones"])
class SolicitudVacacionesViewSet(viewsets.ModelViewSet):
    queryset = SolicitudVacaciones.objects.select_related("empleado").all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedReadOnlyOrRRHH,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = {
        "empleado": ["exact"],
        "estado": ["exact"],
        "fecha_inicio": ["gte", "lte", "exact"],
        "fecha_fin": ["gte", "lte", "exact"],
    }
    search_fields = (
        "empleado__primer_nombre",
        "empleado__apellido_paterno",
        "empleado__numero_empleado",
    )
    ordering_fields = ("fecha_inicio", "fecha_fin", "creado_en")
    ordering = ("-fecha_inicio",)

    def get_serializer_class(self):
        if HAS_CREATE_SERIALIZER:
            from .serializers import SolicitudVacacionesCreateSerializer  # import local para evitar fallo si no existe
            return SolicitudVacacionesCreateSerializer if self.action == "create" else SolicitudVacacionesSerializer
        return SolicitudVacacionesSerializer

    # Transiciones de estado (solo RRHH/Admin/SuperAdmin)
    @action(detail=True, methods=["post"], permission_classes=[IsRRHHEditOnly])
    def aprobar(self, request, pk=None):
        obj = self.get_object()
        if hasattr(obj, "aprobar"):
            obj.aprobar(request.user)
        else:
            # fallback a lÃ³gica simple si el modelo no trae mÃ©todo
            obj.estado = "APROB"
            obj.resuelto_por = request.user if hasattr(obj, "resuelto_por") else None
            obj.resuelto_en = timezone.now() if hasattr(obj, "resuelto_en") else None
            obj.save()
        return Response(SolicitudVacacionesSerializer(obj).data)

    @action(detail=True, methods=["post"], permission_classes=[IsRRHHEditOnly])
    def rechazar(self, request, pk=None):
        obj = self.get_object()
        if hasattr(obj, "rechazar"):
            obj.rechazar(request.user)
        else:
            obj.estado = "RECH"
            obj.resuelto_por = request.user if hasattr(obj, "resuelto_por") else None
            obj.resuelto_en = timezone.now() if hasattr(obj, "resuelto_en") else None
            obj.save()
        return Response(SolicitudVacacionesSerializer(obj).data)

    @action(detail=True, methods=["post"], permission_classes=[IsRRHHEditOnly])
    def cancelar(self, request, pk=None):
        obj = self.get_object()
        if hasattr(obj, "cancelar"):
            obj.cancelar(request.user)
        else:
            obj.estado = "CANC"
            obj.resuelto_por = request.user if hasattr(obj, "resuelto_por") else None
            obj.resuelto_en = timezone.now() if hasattr(obj, "resuelto_en") else None
            obj.save()
        return Response(SolicitudVacacionesSerializer(obj).data)


