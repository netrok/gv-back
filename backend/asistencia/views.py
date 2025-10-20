# asistencia/views.py
from django.utils import timezone
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.views import HealthBaseView
from core.permissions import IsAuthenticatedReadOnlyOrRRHH, IsRRHHEditOnly
from .models import Checada, Justificacion
from .serializers import (
    ChecadaSerializer,
    ChecadaCreateSerializer,
    JustificacionSerializer,
    ResumenAsistenciaDiaSerializer,  # para documentar /resumen/
)
from .utils import evaluar_geocerca


# ========== HEALTH ==========
class HealthView(HealthBaseView):
    app_name = "asistencia"


# ========== CHECADAS ==========
@extend_schema(tags=["asistencia"])
class ChecadaViewSet(viewsets.ModelViewSet):
    """
    CRUD de checadas con filtros, búsqueda y ordering.
    Escritura restringida por roles (core.permissions.IsAuthenticatedReadOnlyOrRRHH).
    """
    queryset = Checada.objects.select_related("empleado", "ubicacion").all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedReadOnlyOrRRHH,)

    # Filtros / búsqueda / ordering
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = {
        "empleado": ["exact"],
        "tipo": ["exact"],
        "dentro_geocerca": ["exact"],
        "ubicacion": ["exact"],
        "fuente": ["exact"],
        # Nota: el rango por fecha se maneja con fecha_desde/fecha_hasta (ver list()).
    }
    # Usa los nombres REALES del modelo Empleado (no propiedades)
    search_fields = (
        "nota",
        "empleado__primer_nombre",
        "empleado__apellido_paterno",
        "empleado__numero_empleado",
    )
    ordering_fields = ("ts", "creado_en")
    ordering = ("-ts",)

    def get_serializer_class(self):
        if self.action in ("create",):
            return ChecadaCreateSerializer
        return ChecadaSerializer

    def perform_create(self, serializer):
        checada = serializer.save(creado_por=self.request.user)
        # Evaluar geocerca si hay coordenadas y ubicación
        if checada.lat is not None and checada.lon is not None and checada.ubicacion_id:
            dist, dentro = evaluar_geocerca(checada.lat, checada.lon, checada.ubicacion)
            Checada.objects.filter(pk=checada.pk).update(distancia_m=dist, dentro_geocerca=dentro)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="empleado", description="ID empleado", required=False, type=int),
            OpenApiParameter(name="tipo", description="IN/OUT", required=False, type=str),
            OpenApiParameter(name="dentro_geocerca", description="true/false", required=False, type=bool),
            OpenApiParameter(name="ubicacion", description="ID ubicacion", required=False, type=int),
            OpenApiParameter(name="fuente", description="MOBILE/WEB/KIOSK/OTHER", required=False, type=str),
            OpenApiParameter(name="fecha_desde", description="YYYY-MM-DD (filtra por ts)", required=False, type=str),
            OpenApiParameter(name="fecha_hasta", description="YYYY-MM-DD (filtra por ts)", required=False, type=str),
            OpenApiParameter(name="search", description="texto en nota/nombre/numero_empleado", required=False, type=str),
            OpenApiParameter(name="ordering", description="ts o creado_en (prefija con - para descendente)", required=False, type=str),
        ],
        description="Lista de checadas con filtros por empleado, tipo, geocerca, ubicación, fuente y rango de fechas.",
    )
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        # Rango por fecha (sobre ts.date)
        fd = request.query_params.get("fecha_desde")
        fh = request.query_params.get("fecha_hasta")
        if fd:
            qs = qs.filter(ts__date__gte=fd)
        if fh:
            qs = qs.filter(ts__date__lte=fh)

        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    # /asistencia/checadas/{id}/recalcular/
    @action(detail=True, methods=["post"], url_path="recalcular")
    def recalcular_geocerca(self, request, pk=None):
        ch = self.get_object()
        if ch.lat is None or ch.lon is None or not ch.ubicacion_id:
            return Response(
                {"detail": "No hay lat/lon o ubicacion para evaluar geocerca."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dist, dentro = evaluar_geocerca(ch.lat, ch.lon, ch.ubicacion)
        ch.distancia_m = dist
        ch.dentro_geocerca = dentro
        ch.save(update_fields=["distancia_m", "dentro_geocerca"])
        return Response(self.get_serializer(ch).data)


# ========== JUSTIFICACIONES ==========
@extend_schema(tags=["asistencia"])
class JustificacionViewSet(viewsets.ModelViewSet):
    """
    Lectura para autenticados; escritura sólo RRHH/Admin/SuperAdmin.
    """
    queryset = Justificacion.objects.select_related("empleado", "resuelto_por").all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsRRHHEditOnly,)
    serializer_class = JustificacionSerializer

    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = {
        "empleado": ["exact"],
        "estado": ["exact"],
        "fecha": ["gte", "lte", "exact"],
    }
    search_fields = (
        "motivo",
        "detalle",
        "empleado__primer_nombre",
        "empleado__apellido_paterno",
        "empleado__numero_empleado",
    )
    ordering_fields = ("fecha", "creado_en", "actualizado_en")
    ordering = ("-fecha", "-creado_en")

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    # /asistencia/justificaciones/{id}/resolver/   body: {"estado": "APROB"|"RECH", "comentario": "..."}
    @action(detail=True, methods=["post"], url_path="resolver")
    def resolver(self, request, pk=None):
        jus = self.get_object()
        nuevo_estado = request.data.get("estado")
        if nuevo_estado not in ("APROB", "RECH"):
            return Response(
                {"detail": "Estado inválido. Usa APROB o RECH."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        jus.estado = nuevo_estado
        jus.resuelto_por = request.user
        jus.resuelto_en = timezone.now()
        jus.save(update_fields=["estado", "resuelto_por", "resuelto_en"])
        return Response(self.get_serializer(jus).data)


# ========== RESUMEN ==========
# /asistencia/resumen/?fecha_desde=YYYY-MM-DD&fecha_hasta=YYYY-MM-DD&empleado=ID
@extend_schema(
    tags=["asistencia"],
    parameters=[
        OpenApiParameter(name="empleado", description="ID empleado (opcional)", required=False, type=int),
        OpenApiParameter(name="fecha_desde", description="YYYY-MM-DD (requerido)", required=True, type=str),
        OpenApiParameter(name="fecha_hasta", description="YYYY-MM-DD (requerido)", required=True, type=str),
    ],
    description="Resumen por día: primera entrada, última salida y conteo de checadas.",
    responses=ResumenAsistenciaDiaSerializer(many=True),
)
class ResumenAsistenciaView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        fd = request.query_params.get("fecha_desde")
        fh = request.query_params.get("fecha_hasta")
        if not fd or not fh:
            return Response(
                {"detail": "fecha_desde y fecha_hasta son requeridas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = Checada.objects.select_related("empleado").filter(ts__date__gte=fd, ts__date__lte=fh)
        emp = request.query_params.get("empleado")
        if emp:
            qs = qs.filter(empleado_id=emp)

        # Por día y empleado: primera IN y última OUT
        datos = {}
        for ch in qs.order_by("empleado_id", "ts").iterator():
            key = (ch.empleado_id, ch.ts.date())
            if key not in datos:
                datos[key] = {
                    "empleado": getattr(ch.empleado, "nombre_completo", str(ch.empleado)),
                    "fecha": f"{ch.ts.date():%Y-%m-%d}",
                    "primera_entrada": None,
                    "ultima_salida": None,
                    "checadas": 0,
                }
            datos[key]["checadas"] += 1
            if ch.tipo == "IN" and datos[key]["primera_entrada"] is None:
                datos[key]["primera_entrada"] = ch.ts.strftime("%H:%M:%S")
            if ch.tipo == "OUT":
                datos[key]["ultima_salida"] = ch.ts.strftime("%H:%M:%S")

        salida = sorted(datos.values(), key=lambda x: (x["fecha"], x["empleado"]))
        return Response(salida)
