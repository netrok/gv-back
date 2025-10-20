from rest_framework import serializers
from .models import Empleado


class EmpleadoSerializer(serializers.ModelSerializer):
    # Lecturas amigables de FKs
    banco_nombre = serializers.CharField(source="banco.nombre", read_only=True)
    escolaridad_nombre = serializers.CharField(source="escolaridad.nombre", read_only=True)
    estado_dom_nombre = serializers.CharField(source="domicilio_estado.nombre", read_only=True)
    municipio_dom_nombre = serializers.CharField(source="domicilio_municipio.nombre", read_only=True)
    estado_nac_nombre = serializers.CharField(source="nacimiento_estado.nombre", read_only=True)
    municipio_nac_nombre = serializers.CharField(source="nacimiento_municipio.nombre", read_only=True)

    unidad_nombre = serializers.CharField(source="unidad_negocio.nombre", read_only=True)
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    area_nombre = serializers.CharField(source="area.nombre", read_only=True)
    departamento_nombre = serializers.CharField(source="departamento.nombre", read_only=True)
    puesto_nombre = serializers.CharField(source="puesto.nombre", read_only=True)
    turno_nombre = serializers.CharField(source="turno.nombre", read_only=True)
    horario_etiqueta = serializers.CharField(source="horario.etiqueta", read_only=True)

    supervisor_nombre = serializers.CharField(source="supervisor.nombre_completo", read_only=True)

    # Info de usuario ligada (solo lectura)
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)
    usuario_email = serializers.EmailField(source="usuario.email", read_only=True)

    class Meta:
        model = Empleado
        fields = "__all__"
        read_only_fields = (
            "creado_en",
            "actualizado_en",
            "creado_por",
            "actualizado_por",
            "usuario",  # <- importantísimo: no editable desde API
        )


class EmpleadoFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = ("id", "numero_empleado", "foto")
