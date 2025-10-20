# backend/reportes/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from core.views import HealthBaseView


@extend_schema(
    tags=["reportes"],
    responses={200: OpenApiTypes.OBJECT},
    description="Healthcheck del mÃ³dulo de Reportes."
)
class HealthView(HealthBaseView):
    app_name = "reportes"


@extend_schema(
    tags=["reportes"],
    summary="Ping de Reportes",
    description="Endpoint simple para verificar disponibilidad del mÃ³dulo de reportes.",
    responses={200: OpenApiTypes.OBJECT},
)
@extend_schema(tags=["reportes"])
class PingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"module": "reportes", "ok": True})

