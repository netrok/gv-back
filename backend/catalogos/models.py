# backend/catalogos/models.py
from django.db import models


class BaseCatalogo(models.Model):
    """Campos comunes a todos los catálogos."""
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
        return f"{self.nombre}"


class Departamento(BaseCatalogo):
    class Meta(BaseCatalogo.Meta):
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"


class Puesto(BaseCatalogo):
    # blank/null opcional: hay empresas que definen puestos globales
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="puestos",
        null=True,
        blank=True,
    )

    class Meta(BaseCatalogo.Meta):
        verbose_name = "Puesto"
        verbose_name_plural = "Puestos"


class Turno(BaseCatalogo):
    # Ejemplo: Matutino, Vespertino, Nocturno
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta(BaseCatalogo.Meta):
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"


class Horario(BaseCatalogo):
    """
    Horario nominal semanal.

    Incluye:
    - etiqueta: descripción legible (ej. 'L-V 09:00-18:00')
    - horas_semanales: referencia
    - dias_laborables_mask: bitmask de días laborables
        * bit 0 = domingo, bit 1 = lunes, ... bit 6 = sábado
        * por defecto: 0b0111110 => L-V
    """
    etiqueta = models.CharField(max_length=128, help_text="Ej. L-V 09:00-18:00")
    horas_semanales = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)

    # Soporte avanzado: máscara de días laborables (compat con necesidades de fin de semana)
    dias_laborables_mask = models.PositiveSmallIntegerField(
        default=0b0111110,
        help_text="Bitmask: 1<<0=Dom, 1<<1=Lun, ... 1<<6=Sáb (por defecto L-V).",
    )

    class Meta(BaseCatalogo.Meta):
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"

    # Helpers
    def trabaja_el_dia(self, dt) -> bool:
        """
        dt puede ser date o datetime.
        Python weekday(): Lunes=0..Domingo=6
        Nuestro bit 0 es Domingo, así que convertimos: Lun(0)->1, ..., Dom(6)->0
        """
        dow = (dt.weekday() + 1) % 7  # 0..6 donde 0=Dom
        return bool(self.dias_laborables_mask & (1 << dow))

    def set_trabaja(self, dow_python: int, trabaja: bool):
        """
        Marca/Desmarca un día (dow_python: 0=Lun..6=Dom).
        """
        mask_dow = (dow_python + 1) % 7
        if trabaja:
            self.dias_laborables_mask |= (1 << mask_dow)
        else:
            self.dias_laborables_mask &= ~(1 << mask_dow)

    def __str__(self):
        return self.nombre


class Banco(BaseCatalogo):
    class Meta(BaseCatalogo.Meta):
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"


class Escolaridad(BaseCatalogo):
    # Ejemplo: Secundaria, Bachillerato, Licenciatura, Maestría, Doctorado
    nivel = models.PositiveSmallIntegerField(
        default=0, help_text="Orden jerárquico (0..n)"
    )

    class Meta(BaseCatalogo.Meta):
        verbose_name = "Escolaridad"
        verbose_name_plural = "Escolaridades"


class Estado(models.Model):
    # MX por defecto; si más países, agregar campo pais
    nombre = models.CharField(max_length=128, db_index=True)
    abreviatura = models.CharField(max_length=10, blank=True, default="")
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name="municipios")
    nombre = models.CharField(max_length=128, db_index=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nombre",)
        unique_together = (("estado", "nombre"),)
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"

    def __str__(self):
        return f"{self.nombre} ({self.estado})"
