from django.urls import path, include

urlpatterns = [
    path("cuentas/", include("cuentas.urls")),
    path("catalogos/", include("catalogos.urls")),
    path("organigrama/", include("organigrama.urls")),
    path("empleados/", include("empleados.urls")),
    path("auditoria/", include("auditoria.urls")),
    path("reportes/", include("reportes.urls")),
    path("configuracion/", include("configuracion.urls")),
    path("notificaciones/", include("notificaciones.urls")),
    path("asistencia/", include("asistencia.urls")),
    path("vacaciones/", include("vacaciones.urls")),
    path("permisos/", include("permisos.urls")),
    path("calendario/", include("calendario.urls")),
    path("vacaciones/", include("vacaciones.urls")),
]
