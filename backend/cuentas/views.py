# backend/cuentas/views.py
from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from core.views import HealthBaseView
from .serializers import UserMeSerializer, PermissionSerializer

User = get_user_model()


# /cuentas/health/
@extend_schema(tags=["health"])
class HealthView(HealthBaseView):
    app_name = "cuentas"


# /cuentas/auth/me/
@extend_schema(tags=["auth"])
@extend_schema(tags=["cuentas"])
@extend_schema(tags=['auth','cuentas'])
class MeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer

    @extend_schema(
        responses={200: UserMeSerializer},
        examples=[
            OpenApiExample(
                "Ejemplo",
                value={
                    "id": 1,
                    "username": "admin",
                    "first_name": "Juan",
                    "last_name": "PÃ©rez",
                    "email": "admin@demo.local",
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": True,
                    "groups": ["RRHH", "Admin"],
                },
            )
        ],
    )
    def get(self, request):
        data = self.get_serializer(request.user).data
        return Response(data)


# /cuentas/auth/permissions/
@extend_schema(tags=["auth"])
@extend_schema(tags=["cuentas"])
@extend_schema(tags=['auth','cuentas'])
class PermissionsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionSerializer

    @extend_schema(
        responses={200: PermissionSerializer},
        examples=[
            OpenApiExample(
                "Ejemplo",
                value={"permissions": ["auth.add_user", "empleados.view_empleado"]},
            )
        ],
    )
    def get(self, request):
        # Permisos efectivos del usuario (propios + por grupos)
        perms = sorted(list(request.user.get_all_permissions()))
        return Response({"permissions": perms})


