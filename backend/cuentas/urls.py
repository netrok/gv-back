from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import HealthView, MeView, PermissionsView

urlpatterns = [
    # Salud del módulo
    path("health/", HealthView.as_view(), name="cuentas-health"),

    # Auth / JWT
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/permissions/", PermissionsView.as_view(), name="auth-permissions"),
]
