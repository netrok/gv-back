# asistencia/serializers.py
from rest_framework import serializers
from core.enums import TipoChecada
from .models import Checada, Justificacion
from organigrama.models import Ubicacion


class ChecadaSerializer(serializers.ModelSerializer):
    # Campos “amigables” (solo salida)
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)
    ubicacion_nombre = serializers.CharField(source="ubicacion.nombre", read_only=True, allow_null=True)

    # Enum claro en el esquema
    tipo = serializers.ChoiceField(choices=TipoChecada.choices)

    # Permitir setear la ubicación por id
    ubicacion_id = serializers.PrimaryKeyRelatedField(
        source="ubicacion",
        queryset=Ubicacion.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Checada
        fields = "__all__"
        extra_kwargs = {
            "ubicacion": {"write_only": True},
            "ts": {"read_only": True},
            "creado_en": {"read_only": True},
            "actualizado_en": {"read_only": True},
        }


class ChecadaCreateSerializer(serializers.ModelSerializer):
    """Serializer de creación (acepta ubicacion_id)."""
    tipo = serializers.ChoiceField(choices=TipoChecada.choices)
    ubicacion_id = serializers.PrimaryKeyRelatedField(
        source="ubicacion",
        queryset=Ubicacion.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Checada
        fields = ("empleado", "tipo", "fuente", "lat", "lon", "ubicacion_id", "nota", "foto")

    def validate(self, attrs):
        lat = attrs.get("lat")
        lon = attrs.get("lon")
        if (lat is None) ^ (lon is None):
            raise serializers.ValidationError("Debes enviar ambos: lat y lon.")
        return attrs


class JustificacionSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)
    # Etiqueta legible del estado sin pisar el campo real
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Justificacion
        fields = "__all__"
        extra_kwargs = {
            "creado_en": {"read_only": True},
            "actualizado_en": {"read_only": True},
            "resuelto_en": {"read_only": True},
        }


# --- Para /asistencia/resumen/ (solo salida) ---
class ResumenAsistenciaDiaSerializer(serializers.Serializer):
    empleado = serializers.CharField(read_only=True)
    fecha = serializers.DateField(read_only=True)
    primera_entrada = serializers.TimeField(allow_null=True, read_only=True)
    ultima_salida = serializers.TimeField(allow_null=True, read_only=True)
    checadas = serializers.IntegerField(read_only=True)
