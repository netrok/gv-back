# backend/vacaciones/models.py
from datetime import date, timedelta
from decimal import Decimal

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from empleados.models import Empleado
from core.enums import EstadoSolicitud  # PEND/APROB/RECH/CANC

User = get_user_model()


# ===============================
# Políticas / Feriados / Balances
# ===============================
class PoliticaVacaciones(models.Model):
    """
    Política por años de antigüedad (rangos) con días asignados y arrastre.
    """
    anios_desde = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
    anios_hasta = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
    dias = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(365)])
    arrastre_maximo = models.PositiveSmallIntegerField(
        default=0, help_text="Días que se pueden arrastrar al siguiente año"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("anios_desde",)
        verbose_name = "Política de vacaciones"
        verbose_name_plural = "Políticas de vacaciones"
        constraints = [
            models.CheckConstraint(
                check=models.Q(anios_hasta__gte=models.F("anios_desde")),
                name="vac_politica_rango_valido",
            ),
        ]

    def __str__(self):
        return f"{self.anios_desde}-{self.anios_hasta}: {self.dias} días (arrastre {self.arrastre_maximo})"


class Feriado(models.Model):
    """Día inhábil (festivo) que no cuenta para vacaciones."""
    fecha = models.DateField(unique=True)
    nombre = models.CharField(max_length=120)

    class Meta:
        ordering = ("fecha",)

    def __str__(self):
        return f"{self.fecha} {self.nombre}"


class BalanceVacaciones(models.Model):
    """
    Balance anual por empleado.
    Se actualiza con el endpoint/command de 'rebuild'.
    """
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="balances_vac")
    anio = models.PositiveIntegerField()

    dias_asignados = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    dias_arrastrados = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    dias_tomados = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    dias_disponibles = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    caduca_el = models.DateField(null=True, blank=True)

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("empleado", "anio"),)
        ordering = ("empleado", "-anio")
        indexes = [models.Index(fields=["empleado", "anio"])]

    def __str__(self):
        return f"{self.empleado} {self.anio}: disp {self.dias_disponibles}"


# ===============================
# Solicitudes (modelo unificado)
# ===============================
class SolicitudVacaciones(models.Model):
    """
    Modelo unificado que soporta:
    - conteo en 'dias_habiles' (entero) y 'dias' (decimal, legacy)
    - estilo de resolución v2 (resuelto_por/en) y legacy v1 (aprobado_por/en/comentario_aprobador)
    """
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="solicitudes_vac")

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    # Nuevo estilo
    dias_habiles = models.PositiveSmallIntegerField(default=0)
    comentario = models.CharField(max_length=255, blank=True, default="")

    # Legacy (se mantiene para compatibilidad; opcional)
    dias = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Días hábiles calculados (legacy decimal, sincronizado con dias_habiles)."
    )
    motivo = models.CharField(max_length=255, blank=True, default="")  # si la versión anterior lo usaba

    estado = models.CharField(
        max_length=5, choices=EstadoSolicitud.choices, default=EstadoSolicitud.PEND, db_index=True
    )

    # Trazas de creación/actualización
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sol_vac_creadas"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    # Resolución v2 (nuevo)
    resuelto_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="vacaciones_resueltas"
    )
    resuelto_en = models.DateTimeField(null=True, blank=True)

    # Resolución legacy v1 (compat)
    aprobado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sol_vac_aprobadas"
    )
    aprobado_en = models.DateTimeField(null=True, blank=True)
    comentario_aprobador = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ("-fecha_inicio", "-creado_en")
        indexes = [
            models.Index(fields=["empleado", "estado", "fecha_inicio", "fecha_fin"]),
        ]

    def __str__(self):
        return f"Vac {self.empleado} {self.fecha_inicio}→{self.fecha_fin} [{self.estado}]"

    # ===== Validaciones =====
    def clean(self):
        errors = {}
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin < self.fecha_inicio:
            errors["fecha_fin"] = "La fecha fin no puede ser menor a la fecha inicio."
        if self.dias is not None and Decimal(self.dias) < 0:
            errors["dias"] = "Los días (legacy) no pueden ser negativos."
        if self.dias_habiles is not None and self.dias_habiles < 0:
            errors["dias_habiles"] = "Los días hábiles no pueden ser negativos."
        if errors:
            raise ValidationError(errors)

    # ===== Cálculo de días =====
    def _feriados_en(self, desde: date, hasta: date):
        """
        Intenta usar fuente centralizada de feriados; si no existe, usa Feriado local.
        """
        try:
            from core.workdays_sources import feriados_en  # opcional
            return list(feriados_en(desde, hasta))
        except Exception:
            return list(Feriado.objects.filter(fecha__gte=desde, fecha__lte=hasta)
                        .values_list("fecha", flat=True))

    def calcular_dias(self) -> int:
        """
        Calcula días hábiles para el empleado respetando su horario (si está soportado).
        Fallback: excluye fines de semana + feriados (modelo local).
        """
        desde, hasta = self.fecha_inicio, self.fecha_fin
        # Intentar función avanzada por empleado
        try:
            from core.workdays import dias_habiles_empleado  # soporta horarios
            fer = self._feriados_en(desde, hasta)
            return int(dias_habiles_empleado(self.empleado, desde, hasta, fer))
        except Exception:
            # Fallback simple: lun-vie, excluyendo Feriado
            feriados = set(self._feriados_en(desde, hasta))
            total = 0
            cur = desde
            while cur <= hasta:
                if cur not in feriados and cur.weekday() < 5:  # 0..4 = lun-vie
                    total += 1
                cur += timedelta(days=1)
            return total

    def _sincronizar_dias(self):
        """
        Mantiene sincronizados dias_habiles (int) y dias (decimal legacy).
        """
        if self.dias_habiles is None:
            self.dias_habiles = 0
        self.dias = Decimal(self.dias_habiles)

    def guardar_con_calculo(self):
        """
        Calcula días y guarda. Rechaza rangos sin días hábiles.
        """
        self.dias_habiles = self.calcular_dias()
        if self.dias_habiles < 1:
            raise ValidationError({"dias_habiles": "El rango no contiene días hábiles."})
        self._sincronizar_dias()
        self.full_clean()
        self.save()

    # ===== Transiciones de estado (actualiza v2 y legacy) =====
    def _resolver(self, nuevo_estado: str, usuario: User | None):
        self.estado = nuevo_estado
        now = timezone.now()
        # v2
        self.resuelto_por = usuario
        self.resuelto_en = now
        # legacy
        self.aprobado_por = usuario
        self.aprobado_en = now
        self.save(update_fields=[
            "estado", "resuelto_por", "resuelto_en",
            "aprobado_por", "aprobado_en", "actualizado_en"
        ])

    def aprobar(self, usuario: User | None):
        self._resolver(EstadoSolicitud.APROB, usuario)

    def rechazar(self, usuario: User | None):
        self._resolver(EstadoSolicitud.RECH, usuario)

    def cancelar(self, usuario: User | None):
        self._resolver(EstadoSolicitud.CANC, usuario)
