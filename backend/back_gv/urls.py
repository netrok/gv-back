# backend/back_gv/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "name": "GV Back API",
        "docs": "/api/docs/",
        "v1": "/api/v1/"
    })

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),

    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # Auth y API principal
    path("api/auth/", include("cuentas.urls")),
    path("api/v1/", include("api.urls")),
]

# Media en dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
