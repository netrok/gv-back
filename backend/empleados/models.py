# backend/empleados/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords

from core.utils import validar_curp, validar_rfc, validar_nss, validar_clabe, validar_cp
from catalogos.models import (
    Banco, Escolaridad, Estado as CatEstado, Municipio as CatMunicipio,
    Departamento, Puesto, Turno, Horario
)
from organigrama.models import UnidadNegocio, Sucursal, Area

User = get_user_model()


def foto_upload_path(instance, filename):
    # media/empleados/{numero_empleado or id}/foto/<filename>
    base = instance.numero_empleado or f"id_{instance.id or 'tmp'}"
    return f"empleados/{base}/foto/{filename}"


class Empleado(models.Model):
    # ===== Identificación del empleado =====
    numero_empleado = models.CharField(max_length=30, unique=True, db_index=True)
    primer_nombre = models.CharField(max_length=60)
    segundo_nombre = models.CharField(max_length=60, blank=True, default="")
    apellido_paterno = models.CharField(max_length=60)
    apellido_materno = models.CharField(max_length=60, blank=True, default="")
    apodo = models.CharField(max_length=60, blank=True, default="")

    SEXO_CHOICES = (("H", "Hombre"), ("M", "Mujer"), ("N", "No especifica"))
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, default="N")

    fecha_nacimiento = models.DateField(null=True, blank=True)
    nacionalidad = models.CharField(max_length=60, blank=True, default="Mexicana")

    estado_civil_choices = (
        ("S", "Soltero(a)"),
        ("C", "Casado(a)"),
        ("U", "Unión libre"),
        ("D", "Divorciado(a)"),
        ("V", "Viudo(a)"),
        ("N", "No especifica"),
    )
    estado_civil = models.CharField(max_length=1, choices=estado_civil_choices, default="N")

    # Lugar de nacimiento (catálogos MX)
    nacimiento_estado = models.ForeignKey(
        CatEstado, on_delete=models.SET_NULL, null=True, blank=True, related_name="nacimientos_estado"
    )
    nacimiento_municipio = models.ForeignKey(
        CatMunicipio, on_delete=models.SET_NULL, null=True, blank=True, related_name="nacimientos_municipio"
    )

    # ===== Documentos de identidad =====
    curp = models.CharField(max_length=18, unique=True, db_index=True)
    rfc = models.CharField(max_length=13, unique=True, db_index=True)
    nss = models.CharField(max_length=11, unique=True, db_index=True, verbose_name="NSS (IMSS)")

    # ===== Contacto =====
    email_personal = models.EmailField(max_length=254, blank=True, default="")
    email_corporativo = models.EmailField(max_length=254, blank=True, default="")
    telefono_movil = models.CharField(max_length=20, blank=True, default="")
    telefono_casa = models.CharField(max_length=20, blank=True, default="")

    # ===== Domicilio actual =====
    calle = models.CharField(max_length=120, blank=True, default="")
    numero_exterior = models.CharField(max_length=20, blank=True, default="")
    numero_interior = models.CharField(max_length=20, blank=True, default="")
    colonia = models.CharField(max_length=120, blank=True, default="")
    codigo_postal = models.CharField(max_length=5, blank=True, default="")
    domicilio_estado = models.ForeignKey(
        CatEstado, on_delete=models.SET_NULL, null=True, blank=True, related_name="domicilios_estado"
    )
    domicilio_municipio = models.ForeignKey(
        CatMunicipio, on_delete=models.SET_NULL, null=True, blank=True, related_name="domicilios_municipio"
    )
    referencia_domicilio = models.CharField(max_length=255, blank=True, default="")
    dom_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    dom_lon = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    # ===== Contacto de emergencia =====
    emergencia_nombre = models.CharField(max_length=120, blank=True, default="")
    emergencia_parentesco = models.CharField(max_length=60, blank=True, default="")
    emergencia_telefono = models.CharField(max_length=20, blank=True, default="")
    emergencia_telefono_alt = models.CharField(max_length=20, blank=True, default="")

    # ===== Salud (básico) =====
    tipo_sangre = models.CharField(max_length=3, blank=True, default="")
    alergias = models.CharField(max_length=255, blank=True, default="")
    padecimientos = models.CharField(max_length=255, blank=True, default="")
    discapacidad = models.CharField(max_length=255, blank=True, default="")

    # ===== Escolaridad =====
    escolaridad = models.ForeignKey(Escolaridad, on_delete=models.SET_NULL, null=True, blank=True)
    carrera = models.CharField(max_length=120, blank=True, default="")
    institucion = models.CharField(max_length=120, blank=True, default="")
    cedula_profesional = models.CharField(max_length=30, blank=True, default="")

    # ===== Datos bancarios =====
    banco = models.ForeignKey(Banco, on_delete=models.SET_NULL, null=True, blank=True)
    cuenta_bancaria = models.CharField(
        max_length=20, blank=True, default="",
        validators=[RegexValidator(r"^\d{6,20}$", "Cuenta debe ser numérica (6-20 dígitos).")]
    )
    clabe = models.CharField(max_length=18, blank=True, default="")
    tarjeta_nomina = models.CharField(max_length=20, blank=True, default="")

    # ===== Empleo / relación laboral =====
    unidad_negocio = models.ForeignKey(UnidadNegocio, on_delete=models.SET_NULL, null=True, blank=True)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    puesto = models.ForeignKey(Puesto, on_delete=models.SET_NULL, null=True, blank=True)
    turno = models.ForeignKey(Turno, on_delete=models.SET_NULL, null=True, blank=True)
    horario = models.ForeignKey(Horario, on_delete=models.SET_NULL, null=True, blank=True)

    supervisor = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reportes_directos"
    )

    fecha_alta = models.DateField(null=True, blank=True)
    fecha_antiguedad = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    motivo_baja = models.CharField(max_length=255, blank=True, default="")

    estatus_choices = (("A", "Activo"), ("B", "Baja"), ("S", "Suspendido"), ("L", "Licencia"))
    estatus = models.CharField(max_length=1, choices=estatus_choices, default="A", db_index=True)

    tipo_contrato_choices = (("I", "Tiempo indeterminado"), ("D", "Tiempo determinado"),
                             ("T", "Temporal/Proyecto"), ("H", "Honorarios"), ("O", "Otro"))
    tipo_contrato = models.CharField(max_length=1, choices=tipo_contrato_choices, default="I")

    tipo_jornada_choices = (("D", "Diurna"), ("N", "Nocturna"), ("M", "Mixta"), ("F", "Flexible"))
    tipo_jornada = models.CharField(max_length=1, choices=tipo_jornada_choices, default="D")

    periodicidad_pago_choices = (("S", "Semanal"), ("Q", "Quincenal"), ("M", "Mensual"))
    periodicidad_pago = models.CharField(max_length=1, choices=periodicidad_pago_choices, default="Q")

    # Salarios
    salario_diario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salario_mensual = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salario_integrado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="SDI")

    # INFONAVIT / FONACOT (registro)
    infonavit_numero = models.CharField(max_length=20, blank=True, default="")
    infonavit_tipo = models.CharField(max_length=10, blank=True, default="", help_text="VSM/UMI/PORCENTAJE")
    infonavit_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    fonacot_numero = models.CharField(max_length=20, blank=True, default="")
    fonacot_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Foto
    foto = models.ImageField(upload_to=foto_upload_path, null=True, blank=True)

    # ==== Vínculo con usuario (1 a 1) ====
    usuario = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="empleado"
    )

    # Trazas
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="empleados_creados"
    )
    actualizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="empleados_actualizados"
    )

    history = HistoricalRecords(inherit=True)

    class Meta:
        ordering = ("apellido_paterno", "apellido_materno", "primer_nombre")
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        indexes = [
            # búsquedas frecuentes en listados/filtros
            models.Index(fields=["estatus"]),
            models.Index(fields=["unidad_negocio", "sucursal"]),
            models.Index(fields=["area", "departamento"]),
            models.Index(fields=["puesto"]),
            models.Index(fields=["usuario"]),
            # claves y docs ya tienen unique + db_index en campos, no repetir
            models.Index(fields=["estatus", "sucursal", "area", "departamento", "puesto"]),
            models.Index(fields=["curp"]),
            models.Index(fields=["rfc"]),
            models.Index(fields=["nss"]),
        ]

    # ===== Validaciones simples usando core.utils =====
    def clean(self):
        errors = {}
        if self.curp and not validar_curp(self.curp):
            errors["curp"] = "CURP inválida."
        if self.rfc and not validar_rfc(self.rfc):
            errors["rfc"] = "RFC inválido."
        if self.nss and not validar_nss(self.nss):
            errors["nss"] = "NSS inválido (11 dígitos)."
        if self.clabe and not validar_clabe(self.clabe):
            errors["clabe"] = "CLABE inválida (18 dígitos)."
        if self.codigo_postal and not validar_cp(self.codigo_postal):
            errors["codigo_postal"] = "CP inválido (5 dígitos)."
        if errors:
            from django.core.exceptions import ValidationError
            raise ValidationError(errors)

    # ===== Presentación =====
    @property
    def nombre_completo(self):
        seg = f" {self.segundo_nombre}" if self.segundo_nombre else ""
        apm = f" {self.apellido_materno}" if self.apellido_materno else ""
        return f"{self.primer_nombre}{seg} {self.apellido_paterno}{apm}".strip()

    def __str__(self):
        return f"{self.numero_empleado} - {self.nombre_completo}"

    # ====== ALIAS DE COMPATIBILIDAD ======
    @property
    def num_empleado(self):
        return self.numero_empleado

    @num_empleado.setter
    def num_empleado(self, value: str):
        self.numero_empleado = value

    @property
    def nombres(self):
        seg = f" {self.segundo_nombre}" if self.segundo_nombre else ""
        return f"{self.primer_nombre}{seg}".strip()

    @nombres.setter
    def nombres(self, value: str):
        value = (value or "").strip()
        if not value:
            self.primer_nombre = ""
            self.segundo_nombre = ""
            return
        partes = value.split()
        self.primer_nombre = partes[0]
        self.segundo_nombre = " ".join(partes[1:]) if len(partes) > 1 else ""

    @property
    def activo(self) -> bool:
        return self.estatus == "A"

    @activo.setter
    def activo(self, value: bool):
        self.estatus = "A" if value else "B"
