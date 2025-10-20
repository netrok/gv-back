from django.db import models
from django.db.models import Q, F
from django.contrib.auth import get_user_model

from empleados.models import Empleado
from core.enums import EstadoSolicitud  # PEND/APROB/RECH/CANC

User = get_user_model()


class TipoPermiso(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    con_goce = models.BooleanField(default=False)
    requiere_evidencia = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "Tipo de permiso"
        verbose_name_plural = "Tipos de permiso"

    def __str__(self):
        return self.nombre


class Permiso(models.Model):
    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name="permisos"
    )
    tipo = models.ForeignKey(
        TipoPermiso, on_delete=models.PROTECT, related_name="permisos"
    )

    # Rango de fechas del permiso (puede ser 1 día)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    # Alternativa por horas: si lo usas, típicamente fecha_inicio == fecha_fin
    horas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Opcional para medio día / horas",
    )

    motivo = models.CharField(max_length=255, blank=True, default="")
    evidencia = models.FileField(
        upload_to="permisos/evidencia/", null=True, blank=True
    )

    estado = models.CharField(
        max_length=5,
        choices=EstadoSolicitud.choices,
        default=EstadoSolicitud.PEND,
        db_index=True,
    )

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="permisos_creados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    aprobado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="permisos_aprobados",
    )
    aprobado_en = models.DateTimeField(null=True, blank=True)
    comentario_aprobador = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        indexes = [
            models.Index(fields=["empleado", "estado"]),
            models.Index(fields=["tipo"]),
            models.Index(fields=["fecha_inicio"]),
            models.Index(fields=["fecha_fin"]),
            models.Index(fields=["empleado", "estado", "fecha_inicio", "fecha_fin"]),
        ]
        constraints = [
            # horas >= 0 o null
            models.CheckConstraint(
                check=Q(horas__isnull=True) | Q(horas__gte=0),
                name="perm_horas_no_negativas",
            ),
            # si horas no es null -> fecha_inicio == fecha_fin
            models.CheckConstraint(
                check=Q(horas__isnull=True) | Q(fecha_inicio=F("fecha_fin")),
                name="perm_horas_un_solo_dia",
            ),
            # fecha_fin >= fecha_inicio
            models.CheckConstraint(
                check=Q(fecha_fin__gte=F("fecha_inicio")),
                name="perm_rango_fechas_valido",
            ),
        ]

    def __str__(self):
        return f"{self.empleado} {self.tipo} {self.fecha_inicio}→{self.fecha_fin} [{self.estado}]"

    # Validaciones de modelo (lado Python)
    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            errors["fecha_fin"] = "La fecha fin no puede ser menor a la fecha inicio."

        if self.horas is not None:
            if self.horas < 0:
                errors["horas"] = "Las horas no pueden ser negativas."
            if (
                self.horas > 0
                and self.fecha_inicio
                and self.fecha_fin
                and self.fecha_inicio != self.fecha_fin
            ):
                errors["horas"] = "Si capturas 'horas', usa el mismo día en inicio y fin."

        if errors:
            raise ValidationError(errors)
