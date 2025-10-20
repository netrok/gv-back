# backend/organigrama/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class BaseOrg(models.Model):
    """Campos comunes para catálogo organizacional."""
    clave = models.CharField(max_length=32, unique=True)
    nombre = models.CharField(max_length=255, db_index=True)
    descripcion = models.TextField(blank=True, default="")
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre


class UnidadNegocio(BaseOrg):
    """Unidad estratégica o marca/linea."""
    class Meta(BaseOrg.Meta):
        verbose_name = "Unidad de negocio"
        verbose_name_plural = "Unidades de negocio"


class Sucursal(BaseOrg):
    """Sede/tienda/oficina física (pertenece opcionalmente a una unidad de negocio)."""
    unidad = models.ForeignKey(
        UnidadNegocio, on_delete=models.PROTECT, related_name="sucursales",
        null=True, blank=True
    )
    codigo_postal = models.CharField(max_length=10, blank=True, default="")
    ciudad = models.CharField(max_length=128, blank=True, default="")
    estado = models.CharField(max_length=128, blank=True, default="")
    direccion = models.CharField(max_length=255, blank=True, default="")
    telefono = models.CharField(max_length=32, blank=True, default="")

    class Meta(BaseOrg.Meta):
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"


class Area(BaseOrg):
    """
    Área/departamento dentro de una sucursal.
    Puede ser jerárquica (parent) o global si no se asigna sucursal.
    """
    sucursal = models.ForeignKey(
        Sucursal, on_delete=models.PROTECT, related_name="areas",
        null=True, blank=True
    )
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, related_name="subareas",
        null=True, blank=True
    )

    class Meta(BaseOrg.Meta):
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        indexes = [
            models.Index(fields=["sucursal", "nombre"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["sucursal", "clave"],
                name="uniq_area_clave_por_sucursal"
            )
        ]


class Ubicacion(models.Model):
    """
    Punto de geofencing (para asistencia, seguridad, etc.).
    Asociable a sucursal o área. Debe tener al menos uno de los dos.
    """
    nombre = models.CharField(max_length=255)
    sucursal = models.ForeignKey(
        Sucursal, on_delete=models.PROTECT, related_name="ubicaciones",
        null=True, blank=True
    )
    area = models.ForeignKey(
        Area, on_delete=models.PROTECT, related_name="ubicaciones",
        null=True, blank=True
    )

    lat = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    lon = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    radio_m = models.PositiveIntegerField(
        default=100, validators=[MinValueValidator(10)],
        help_text="Radio de geocerca en metros (mínimo 10)"
    )

    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        indexes = [
            models.Index(fields=["activo", "sucursal", "area"]),
            models.Index(fields=["nombre"]),
        ]
        constraints = [
            # Al menos uno: sucursal o área
            models.CheckConstraint(
                check=(
                    models.Q(sucursal__isnull=False) |
                    models.Q(area__isnull=False)
                ),
                name="ubicacion_owner_requerido"
            ),
            # Unicidad por nombre dentro de la sucursal (si aplica)
            models.UniqueConstraint(
                fields=["sucursal", "nombre"],
                condition=models.Q(sucursal__isnull=False),
                name="uniq_ubicacion_por_sucursal_nombre"
            ),
            # Unicidad por nombre dentro del área (si aplica)
            models.UniqueConstraint(
                fields=["area", "nombre"],
                condition=models.Q(area__isnull=False),
                name="uniq_ubicacion_por_area_nombre"
            ),
        ]

    def __str__(self):
        owner = self.area or self.sucursal
        # evita None si ambos están vacíos (solo por seguridad)
        owner_txt = str(owner) if owner else "sin-owner"
        return f"{self.nombre} [{owner_txt}]"
