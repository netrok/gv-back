from django.contrib import admin
from .models import (
    PoliticaVacaciones,
    Feriado as VacFeriado,
    BalanceVacaciones,
    SolicitudVacaciones,
)

@admin.register(PoliticaVacaciones)
class PoliticaVacacionesAdmin(admin.ModelAdmin):
    list_display = ("anios_desde", "anios_hasta", "dias", "arrastre_maximo", "activo")
    list_filter = ("activo",)
    search_fields = ("anios_desde", "anios_hasta")
    ordering = ("anios_desde",)

@admin.register(VacFeriado)
class FeriadoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "nombre")
    ordering = ("fecha",)
    date_hierarchy = "fecha"
    search_fields = ("nombre",)

@admin.register(BalanceVacaciones)
class BalanceVacacionesAdmin(admin.ModelAdmin):
    list_display = (
        "empleado", "anio",
        "dias_asignados", "dias_arrastrados", "dias_tomados", "dias_disponibles",
        "caduca_el", "actualizado_en",
    )
    list_filter = ("anio",)
    search_fields = ("empleado__numero_empleado", "empleado__primer_nombre", "empleado__apellido_paterno")
    date_hierarchy = "caduca_el"
    autocomplete_fields = ("empleado",)
    ordering = ("-anio", "empleado")

@admin.register(SolicitudVacaciones)
class SolicitudVacacionesAdmin(admin.ModelAdmin):
    # Mostrar dias_habiles o, si no existe, dias legacy
    def dias_calculados(self, obj):
        return getattr(obj, "dias_habiles", None) if getattr(obj, "dias_habiles", None) is not None else getattr(obj, "dias", None)
    dias_calculados.short_description = "Días"

    list_display = (
        "empleado", "fecha_inicio", "fecha_fin", "dias_calculados",
        "estado", "resuelto_por", "resuelto_en", "creado_en",
    )
    list_filter = ("estado", "fecha_inicio", "fecha_fin", "creado_en")
    search_fields = (
        "empleado__numero_empleado", "empleado__primer_nombre", "empleado__apellido_paterno",
        "comentario", "motivo", "comentario_aprobador",
    )
    date_hierarchy = "fecha_inicio"
    ordering = ("-fecha_inicio", "-creado_en")
    autocomplete_fields = ("empleado", "creado_por", "resuelto_por", "aprobado_por")
    readonly_fields = ("creado_en", "actualizado_en", "resuelto_en", "aprobado_en")

    actions = ("accion_aprobar", "accion_rechazar", "accion_cancelar")

    def _do_transition(self, request, queryset, metodo, nombre):
        total = 0
        for obj in queryset:
            if hasattr(obj, metodo):
                getattr(obj, metodo)(request.user)
                total += 1
        self.message_user(request, f"{nombre}: {total} solicitud(es) actualizada(s).")

    def accion_aprobar(self, request, queryset):
        self._do_transition(request, queryset, "aprobar", "Aprobadas")
    accion_aprobar.short_description = "Aprobar seleccionadas"

    def accion_rechazar(self, request, queryset):
        self._do_transition(request, queryset, "rechazar", "Rechazadas")
    accion_rechazar.short_description = "Rechazar seleccionadas"

    def accion_cancelar(self, request, queryset):
        self._do_transition(request, queryset, "cancelar", "Canceladas")
    accion_cancelar.short_description = "Cancelar seleccionadas"
