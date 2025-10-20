# backend/notificaciones/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated  # cambia a AllowAny si quieres pÃºblico
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from core.views import HealthBaseView


@extend_schema(
    tags=["notificaciones"],
    responses={200: OpenApiTypes.OBJECT},
    description="Healthcheck del mÃ³dulo de Notificaciones."
)
class HealthView(HealthBaseView):
    app_name = "notificaciones"


@extend_schema(
    tags=["notificaciones"],
    summary="Ping de Notificaciones",
    description="Endpoint simple para verificar disponibilidad del mÃ³dulo de notificaciones.",
    responses={200: OpenApiTypes.OBJECT},
)
@extend_schema(tags=["notificaciones"])
class PingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"module": "notificaciones", "ok": True})

