from rest_framework import serializers
from .models import TipoPermiso, Permiso


class TipoPermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPermiso
        fields = "__all__"


class PermisoSerializer(serializers.ModelSerializer):
    # Campos derivados de solo lectura
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)
    tipo_nombre = serializers.CharField(source="tipo.nombre", read_only=True)

    # Evitar enum duplicado en el esquema; el modelo ya valida por choices
    estado = serializers.CharField(read_only=True)

    class Meta:
        model = Permiso
        fields = "__all__"
        read_only_fields = (
            "estado",
            "creado_por",
            "creado_en",
            "actualizado_en",
            "aprobado_por",
            "aprobado_en",
            "comentario_aprobador",
            "empleado_nombre",
            "tipo_nombre",
        )
