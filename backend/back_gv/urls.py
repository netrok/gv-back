# backend/back_gv/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import JsonResponse

# Si tienes esta view utilitaria
from core.views_misc import version  # <-- asegúrate que exista

def home(request):
    return JsonResponse({
        "name": "GV Back API",
        "docs": "/api/docs/",
        "schema": "/api/schema/",
        "v1": "/api/v1/",
    })

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),

    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("swagger/", RedirectView.as_view(url="/api/docs/", permanent=False), name="swagger-redirect"),

    # API v1 (único include)
    path("api/v1/", include("api.urls")),

    # Versión de API
    path("api/version/", version, name="api-version"),
]

# Media en dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
