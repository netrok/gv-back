from django.urls import path
from .views import MeView, PermissionsView, HealthView
from .views_auth import JWTObtainPairView, JWTRefreshView

app_name = "cuentas"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/permissions/", PermissionsView.as_view(), name="auth-permissions"),
    path("auth/token/", JWTObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", JWTRefreshView.as_view(), name="token_refresh"),
]
