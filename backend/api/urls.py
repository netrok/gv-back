# backend/api/urls.py
from django.urls import path, include

urlpatterns = [
    path("cuentas/",       include(("cuentas.urls", "cuentas"), namespace="cuentas")),
    path("catalogos/",     include("catalogos.urls")),
    path("organigrama/",   include("organigrama.urls")),
    path("empleados/",     include("empleados.urls")),
    path("asistencia/",    include("asistencia.urls")),
    path("permisos/",      include("permisos.urls")),
    path("vacaciones/",    include("vacaciones.urls")),
    path("calendario/",    include("calendario.urls")),

    # módulos “ping/health” ya creados
    path("reportes/",      include("reportes.urls")),
    path("configuracion/", include("configuracion.urls")),
    path("notificaciones/",include("notificaciones.urls")),
    path("auditoria/",     include("auditoria.urls")),
]
