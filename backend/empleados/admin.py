from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from .models import Empleado


@admin.register(Empleado)
class EmpleadoAdmin(SimpleHistoryAdmin):
    # ====== Listado ======
    list_display = (
        "numero_empleado",
        "nombre_corto",
        "unidad_negocio",
        "sucursal",
        "departamento",
        "puesto",
        "estatus",
        "fecha_alta",
        "mini_foto",
    )
    list_display_links = ("numero_empleado", "nombre_corto")
    ordering = ("apellido_paterno", "apellido_materno", "primer_nombre")
    date_hierarchy = "fecha_alta"
    list_per_page = 50

    # ====== Búsqueda ======
    search_fields = (
        "numero_empleado",
        "primer_nombre", "segundo_nombre",
        "apellido_paterno", "apellido_materno",
        "rfc", "curp", "nss",
        "email_personal", "email_corporativo",
        "sucursal__nombre", "departamento__nombre", "puesto__nombre",
        "supervisor__primer_nombre", "supervisor__apellido_paterno",
    )

    # ====== Filtros ======
    list_filter = (
        "estatus", "sexo",
        "unidad_negocio", "sucursal", "area", "departamento", "puesto",
        "turno", "horario",
        "banco", "escolaridad",
    )

    # ====== Optimización ======
    list_select_related = (
        "unidad_negocio", "sucursal", "area", "departamento", "puesto",
        "turno", "horario", "banco", "escolaridad", "supervisor",
    )

    # ====== Raw IDs ======
    raw_id_fields = (
        "usuario",
        "banco", "escolaridad",
        "domicilio_estado", "domicilio_municipio",
        "nacimiento_estado", "nacimiento_municipio",
        "unidad_negocio", "sucursal", "area", "departamento",
        "puesto", "turno", "horario",
        "supervisor",
        "creado_por", "actualizado_por",
    )

    # ====== Readonly y fieldsets ======
    readonly_fields = ("nombre_completo_admin", "creado_en", "actualizado_en", "creado_por", "actualizado_por", "preview_foto")

    fieldsets = (
        ("Identificación", {
            "fields": (
                ("numero_empleado", "estatus"),
                ("primer_nombre", "segundo_nombre"),
                ("apellido_paterno", "apellido_materno"),
                ("apodo", "sexo"),
                ("fecha_nacimiento", "nacionalidad", "estado_civil"),
                "nombre_completo_admin",
                "usuario",
            )
        }),
        ("Lugar de nacimiento", {
            "fields": (("nacimiento_estado", "nacimiento_municipio"),)
        }),
        ("Documentos", {
            "fields": (("curp", "rfc", "nss"),)
        }),
        ("Contacto", {
            "fields": (
                ("email_personal", "email_corporativo"),
                ("telefono_movil", "telefono_casa"),
            )
        }),
        ("Domicilio", {
            "fields": (
                ("calle", "numero_exterior", "numero_interior"),
                "colonia", ("codigo_postal",),
                ("domicilio_estado", "domicilio_municipio"),
                "referencia_domicilio",
                ("dom_lat", "dom_lon"),
            )
        }),
        ("Contacto de emergencia", {
            "fields": (
                ("emergencia_nombre", "emergencia_parentesco"),
                ("emergencia_telefono", "emergencia_telefono_alt"),
            )
        }),
        ("Salud", {
            "fields": (("tipo_sangre", "alergias"), ("padecimientos", "discapacidad"))
        }),
        ("Escolaridad", {
            "fields": (("escolaridad", "carrera"), ("institucion", "cedula_profesional"))
        }),
        ("Bancarios", {
            "fields": (("banco", "cuenta_bancaria"), ("clabe", "tarjeta_nomina"))
        }),
        ("Laboral", {
            "fields": (
                ("unidad_negocio", "sucursal"),
                ("area", "departamento", "puesto"),
                ("turno", "horario"),
                "supervisor",
                ("fecha_alta", "fecha_antiguedad", "fecha_baja"),
                "motivo_baja",
                ("tipo_contrato", "tipo_jornada", "periodicidad_pago"),
            )
        }),
        ("Salarios", {
            "fields": (("salario_diario", "salario_mensual", "salario_integrado"),)
        }),
        ("INFONAVIT / FONACOT", {
            "fields": (
                ("infonavit_numero", "infonavit_tipo", "infonavit_descuento"),
                ("fonacot_numero", "fonacot_descuento"),
            )
        }),
        ("Foto", {
            "fields": ("foto", "preview_foto")
        }),
        ("Trazas", {
            "classes": ("collapse",),
            "fields": (("creado_en", "actualizado_en"), ("creado_por", "actualizado_por"))
        }),
    )

    # ====== Métodos auxiliares ======
    def nombre_corto(self, obj):
        return f"{obj.apellido_paterno} {obj.apellido_materno}, {obj.primer_nombre}".strip()
    nombre_corto.short_description = "Nombre"

    def mini_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:4px;" />', obj.foto.url)
        return "—"
    mini_foto.short_description = "Foto"

    def preview_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-height:180px;max-width:180px;object-fit:cover;border-radius:8px;border:1px solid #ddd;" />', obj.foto.url)
        return "—"
    preview_foto.short_description = "Vista previa"

    def nombre_completo_admin(self, obj):
        return getattr(obj, "nombre_completo", "")
    nombre_completo_admin.short_description = "Nombre completo (auto)"
