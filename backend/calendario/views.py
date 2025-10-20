from datetime import date, timedelta
from typing import Dict, List, Tuple

from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from empleados.models import Empleado
from vacaciones.models import SolicitudVacaciones
from permisos.models import Permiso
from .serializers import CalendarioResponseSerializer  # respuesta documentada


def _daterange(d1: date, d2: date):
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)


def _empleados_filtrados(params, user):
    qs = Empleado.objects.select_related(
        "unidad_negocio", "sucursal", "area", "departamento", "puesto", "usuario"
    )
    # Filtros organizacionales
    mapping = {
        "unidad_negocio": "unidad_negocio_id",
        "sucursal": "sucursal_id",
        "area": "area_id",
        "departamento": "departamento_id",
        "puesto": "puesto_id",
        "empleado": "id",
        "estatus": "estatus",
    }
    for k, field in mapping.items():
        v = params.get(k)
        if v:
            qs = qs.filter(**{field: v})

    # Seguridad: usuario no staff solo ve su propio registro
    if user.is_authenticated and not user.is_staff:
        if hasattr(user, "empleado"):
            qs = qs.filter(id=user.empleado_id)
        else:
            qs = qs.none()
    return qs


@extend_schema(
    tags=["calendario"],
    parameters=[
        OpenApiParameter("desde", str, description="YYYY-MM-DD (requerido)", required=True),
        OpenApiParameter("hasta", str, description="YYYY-MM-DD (requerido)", required=True),
        OpenApiParameter("empleado", int, description="ID empleado (opcional)", required=False),
        OpenApiParameter("unidad_negocio", int, description="ID unidad (opcional)", required=False),
        OpenApiParameter("sucursal", int, description="ID sucursal (opcional)", required=False),
        OpenApiParameter("area", int, description="ID área (opcional)", required=False),
        OpenApiParameter("departamento", int, description="ID departamento (opcional)", required=False),
        OpenApiParameter("puesto", int, description="ID puesto (opcional)", required=False),
        OpenApiParameter("estado", str, description="Filtra estado: PEND/APROB/RECH/CANC (opcional)", required=False),
        OpenApiParameter("incluir_pendientes", bool, description="true/false (default true)", required=False),
        OpenApiParameter("incluir_rechazadas", bool, description="true/false (default false)", required=False),
        OpenApiParameter("incluir_canceladas", bool, description="true/false (default false)", required=False),
    ],
    description=(
        "Devuelve un calendario por empleado y día con ausencias de **vacaciones** y **permisos**. "
        "Respeta filtros organizacionales y de estado. Usuario no staff solo ve su propio calendario."
    ),
    responses=CalendarioResponseSerializer,
)
class CalendarioAusenciasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # --- Validación de rango ---
        s_desde = request.query_params.get("desde")
        s_hasta = request.query_params.get("hasta")
        if not s_desde or not s_hasta:
            return Response({"detail": "desde y hasta son requeridos (YYYY-MM-DD)."}, status=400)
        try:
            d1 = parse_date(s_desde)
            d2 = parse_date(s_hasta)
            if not d1 or not d2 or d2 < d1:
                raise ValueError
            if (d2 - d1).days > 62:
                # Protección: máximo 2 meses para evitar respuestas gigantes
                return Response({"detail": "Rango demasiado amplio. Máximo 62 días."}, status=400)
        except Exception:
            return Response({"detail": "Formato de fecha inválido."}, status=400)

        # Flags de estados
        incluir_pend = request.query_params.get("incluir_pendientes", "true").lower() != "false"
        incluir_rech = request.query_params.get("incluir_rechazadas", "false").lower() == "true"
        incluir_canc = request.query_params.get("incluir_canceladas", "false").lower() == "true"
        estado_single = request.query_params.get("estado")

        estados: List[str] = []
        if estado_single:
            estados = [estado_single]
        else:
            if incluir_pend:
                estados.append("PEND")
            estados.append("APROB")
            if incluir_rech:
                estados.append("RECH")
            if incluir_canc:
                estados.append("CANC")

        # --- Empleados objetivos ---
        empleados = list(_empleados_filtrados(request.query_params, request.user))

        # Si no hay empleados que ver, corta rápido
        if not empleados:
            return Response({
                "desde": f"{d1:%Y-%m-%d}",
                "hasta": f"{d2:%Y-%m-%d}",
                "dias": [],
                "items": [],
                "estados_solicitud_incluidos": estados,
            })

        emp_ids = [e.id for e in empleados]

        # --- Traer vacaciones y permisos traslapados con el rango ---
        vac_qs = (SolicitudVacaciones.objects
                  .select_related("empleado")
                  .filter(empleado_id__in=emp_ids,
                          estado__in=estados,
                          fecha_inicio__lte=d2,
                          fecha_fin__gte=d1))
        per_qs = (Permiso.objects
                  .select_related("empleado", "tipo")
                  .filter(empleado_id__in=emp_ids,
                          estado__in=estados,
                          fecha_inicio__lte=d2,
                          fecha_fin__gte=d1))

        # --- Armar mapa por (empleado_id, fecha) -> ausencia ---
        cells: Dict[Tuple[int, date], Dict] = {}

        for s in vac_qs:
            cur_i = max(d1, s.fecha_inicio)
            cur_f = min(d2, s.fecha_fin)
            for d in _daterange(cur_i, cur_f):
                cells[(s.empleado_id, d)] = {
                    "tipo_ausencia": "VAC",
                    "subtipo": "Vacaciones",
                    "estado_solicitud": s.estado,
                    "id_solicitud": s.id,
                }

        for p in per_qs:
            cur_i = max(d1, p.fecha_inicio)
            cur_f = min(d2, p.fecha_fin)
            for d in _daterange(cur_i, cur_f):
                # prioridad a permiso sobre vacaciones
                cells[(p.empleado_id, d)] = {
                    "tipo_ausencia": "PERM",
                    "subtipo": getattr(p.tipo, "nombre", "Permiso"),
                    "estado_solicitud": p.estado,
                    "id_solicitud": p.id,
                }

        # --- Construcción de respuesta: items por empleado con vector de días ---
        dias = [f"{d:%Y-%m-%d}" for d in _daterange(d1, d2)]
        items = []
        for e in empleados:
            row = {
                "empleado": {
                    "id": e.id,
                    "numero_empleado": e.numero_empleado,
                    "nombre": e.nombre_completo,
                    "sucursal": getattr(e.sucursal, "nombre", None),
                    "area": getattr(e.area, "nombre", None),
                    "departamento": getattr(e.departamento, "nombre", None),
                    "puesto": getattr(e.puesto, "nombre", None),
                },
                "dias": [],
            }
            for d in _daterange(d1, d2):
                info = cells.get((e.id, d))
                row["dias"].append({
                    "fecha": f"{d:%Y-%m-%d}",
                    "ausencia": info,  # puede ser None si no hay ausencia
                })
            items.append(row)

        return Response({
            "desde": f"{d1:%Y-%m-%d}",
            "hasta": f"{d2:%Y-%m-%d}",
            "dias": dias,   # útil para armar headers en el front
            "items": items,
            "estados_solicitud_incluidos": estados,
        })
