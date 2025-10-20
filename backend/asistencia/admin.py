# asistencia/admin.py
from django.contrib import admin
from .models import Checada, Justificacion


@admin.register(Checada)
class ChecadaAdmin(admin.ModelAdmin):
    list_display = (
        "id", "empleado", "tipo", "fuente",
        "dentro_geocerca", "distancia_m",
        "ts", "creado_en", "actualizado_en",
    )
    list_filter = ("tipo", "fuente", "dentro_geocerca", "ts", "creado_en")
    search_fields = (
        "empleado__num_empleado",
        "empleado__nombres",
        "empleado__apellido_paterno",
        "nota",
    )
    date_hierarchy = "ts"
    autocomplete_fields = ("empleado", "ubicacion", "creado_por")
    readonly_fields = ("ts", "creado_en", "actualizado_en")
    list_select_related = ("empleado", "ubicacion")
    ordering = ("-ts",)
    list_per_page = 50


@admin.register(Justificacion)
class JustificacionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "empleado", "fecha", "estado",
        "resuelto_por", "resuelto_en",
        "creado_en", "actualizado_en",
    )
    list_filter = ("estado", "fecha", "creado_en")
    search_fields = (
        "empleado__num_empleado",
        "empleado__nombres",
        "empleado__apellido_paterno",
        "motivo",
    )
    date_hierarchy = "fecha"
    autocomplete_fields = ("empleado", "resuelto_por", "creado_por")
    readonly_fields = ("creado_en", "actualizado_en")
    list_select_related = ("empleado",)
    ordering = ("-fecha", "-creado_en")
    list_per_page = 50
