from django.contrib import admin
from .models import UnidadNegocio, Sucursal, Area, Ubicacion

@admin.register(UnidadNegocio)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "activo", "actualizado_en")
    search_fields = ("clave", "nombre")
    list_filter = ("activo",)

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "unidad", "ciudad", "estado", "activo")
    search_fields = ("clave", "nombre", "ciudad", "estado")
    list_filter = ("activo", "unidad")

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "sucursal", "parent", "activo")
    search_fields = ("clave", "nombre", "sucursal__nombre", "parent__nombre")
    list_filter = ("activo", "sucursal")

@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sucursal", "area", "lat", "lon", "radio_m", "activo")
    search_fields = ("nombre", "sucursal__nombre", "area__nombre")
    list_filter = ("activo", "sucursal", "area")
