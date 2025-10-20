# backend/configuracion/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated  # usa AllowAny si quieres pÃºblico
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from core.views import HealthBaseView


@extend_schema(
    tags=["configuracion"],
    responses={200: OpenApiTypes.OBJECT},
    description="Healthcheck del mÃ³dulo de ConfiguraciÃ³n."
)
class HealthView(HealthBaseView):
    app_name = "configuracion"


@extend_schema(
    tags=["configuracion"],
    summary="Ping de ConfiguraciÃ³n",
    description="Endpoint simple para verificar disponibilidad del mÃ³dulo de configuraciÃ³n.",
    responses={200: OpenApiTypes.OBJECT},
)
@extend_schema(tags=["configuracion"])
class PingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"module": "configuracion", "ok": True})

