# backend/core/views.py
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from .serializers import HealthSerializer

class HealthBaseView(GenericAPIView):
    """
    Vista base de salud para reutilizar en cada app.
    Ejemplo: class HealthView(HealthBaseView): app_name = "asistencia"
    """
    permission_classes = (AllowAny,)
    serializer_class = HealthSerializer
    app_name = "core"

    @extend_schema(
        tags=["health"],
        responses=HealthSerializer,
        summary="Healthcheck de la aplicación",
        description="Devuelve un JSON simple para verificar disponibilidad del servicio."
    )
    def get(self, request):
        data = {"status": "ok", "app": self.app_name}
        return Response(data)
