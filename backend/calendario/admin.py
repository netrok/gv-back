from django.contrib import admin
from .models import Feriado  # proxy de vacaciones.Feriado

@admin.register(Feriado)
class FeriadoCalendarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "nombre")
    ordering = ("fecha",)
    date_hierarchy = "fecha"
    search_fields = ("nombre",)
