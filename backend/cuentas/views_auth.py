from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

@extend_schema(tags=["auth", "cuentas"])
class JWTObtainPairView(TokenObtainPairView):
    pass

@extend_schema(tags=["auth", "cuentas"])
class JWTRefreshView(TokenRefreshView):
    pass
