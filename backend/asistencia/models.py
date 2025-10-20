# asistencia/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

from empleados.models import Empleado
from organigrama.models import Ubicacion
from core.enums import TipoChecada, EstadoSolicitud  # IN/OUT y PEND/APROB/RECH/CANC

User = get_user_model()


class Checada(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="checadas")

    # IN / OUT (enum unificado)
    tipo = models.CharField(max_length=4, choices=TipoChecada.choices)

    # Marca de tiempo de la checada (evento), independiente de creación del registro
    ts = models.DateTimeField(auto_now_add=True, db_index=True)

    # Origen de la checada
    FUENTE_CHOICES = (
        ("MOBILE", "Móvil"),
        ("WEB", "Web"),
        ("KIOSK", "Kiosco"),
        ("OTHER", "Otro"),
    )
    fuente = models.CharField(max_length=10, choices=FUENTE_CHOICES, default="MOBILE")

    # Geolocalización reportada por el cliente
    lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    lon = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    # Evaluación de geocerca
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True)
    distancia_m = models.PositiveIntegerField(null=True, blank=True, help_text="Distancia al centro de geocerca (m)")
    dentro_geocerca = models.BooleanField(default=False)

    # Evidencia opcional
    foto = models.ImageField(upload_to="asistencia/checada/foto/", null=True, blank=True)
    nota = models.CharField(max_length=255, blank=True, default="")

    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="checadas_creadas")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)   # ← agregado para consistencia

    class Meta:
        ordering = ("-ts",)
        indexes = [
            models.Index(fields=["empleado", "ts"]),
            models.Index(fields=["dentro_geocerca"]),
        ]

    def __str__(self):
        return f"{self.empleado} {self.tipo} {self.ts:%Y-%m-%d %H:%M}"


class Justificacion(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="justificaciones")
    fecha = models.DateField(db_index=True)
    motivo = models.CharField(max_length=255)
    detalle = models.TextField(blank=True, default="")
    evidencia = models.FileField(upload_to="asistencia/justificaciones/", null=True, blank=True)

    # Estado (enum unificado)
    estado = models.CharField(
        max_length=5,
        choices=EstadoSolicitud.choices,
        default=EstadoSolicitud.PEND,
        db_index=True,
    )
    resuelto_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="justificaciones_resueltas")
    resuelto_en = models.DateTimeField(null=True, blank=True)

    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="justificaciones_creadas")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-fecha", "-creado_en")
        indexes = [
            models.Index(fields=["empleado", "fecha"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        return f"Justificación {self.empleado} {self.fecha} ({self.estado})"
