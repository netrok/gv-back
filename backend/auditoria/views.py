# backend/auditoria/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated  # usa AllowAny si quieres pÃºblico
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from core.views import HealthBaseView


@extend_schema(
    tags=["auditoria"],
    responses={200: OpenApiTypes.OBJECT},
    description="Healthcheck del mÃ³dulo de AuditorÃ­a."
)
class HealthView(HealthBaseView):
    app_name = "auditoria"


@extend_schema(
    tags=["auditoria"],
    summary="Ping de AuditorÃ­a",
    description="Endpoint simple para verificar disponibilidad del mÃ³dulo de auditorÃ­a.",
    responses={200: OpenApiTypes.OBJECT},
)
@extend_schema(tags=["auditoria"])
class PingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"module": "auditoria", "ok": True})

