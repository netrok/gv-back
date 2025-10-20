from rest_framework import serializers
from core.enums import EstadoSolicitud, TipoAusencia


class AusenciaSerializer(serializers.Serializer):
    """Resumen de una ausencia (solo salida)."""
    tipo_ausencia = serializers.ChoiceField(choices=TipoAusencia.choices, read_only=True)
    subtipo = serializers.CharField(read_only=True)
    estado_solicitud = serializers.ChoiceField(choices=EstadoSolicitud.choices, read_only=True)
    id_solicitud = serializers.IntegerField(read_only=True)

    class Meta:
        ref_name = "CalendarioAusencia"  # evita choques de nombre en OpenAPI


class CalendarioDiaCellSerializer(serializers.Serializer):
    """Celda de calendario para un día de un empleado."""
    fecha = serializers.DateField(read_only=True)
    ausencia = AusenciaSerializer(allow_null=True, read_only=True)

    class Meta:
        ref_name = "CalendarioDiaCell"


class CalendarioEmpleadoInfoSerializer(serializers.Serializer):
    """Información básica del empleado mostrada en el calendario."""
    id = serializers.IntegerField(read_only=True)
    numero_empleado = serializers.CharField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    sucursal = serializers.CharField(allow_null=True, read_only=True)
    area = serializers.CharField(allow_null=True, read_only=True)
    departamento = serializers.CharField(allow_null=True, read_only=True)
    puesto = serializers.CharField(allow_null=True, read_only=True)

    class Meta:
        ref_name = "CalendarioEmpleadoInfo"


class CalendarioEmpleadoRowSerializer(serializers.Serializer):
    """Fila del calendario: un empleado y sus días."""
    empleado = CalendarioEmpleadoInfoSerializer(read_only=True)
    dias = CalendarioDiaCellSerializer(many=True, read_only=True)

    class Meta:
        ref_name = "CalendarioEmpleadoRow"


class CalendarioResponseSerializer(serializers.Serializer):
    """Respuesta del endpoint de calendario."""
    desde = serializers.DateField(read_only=True)
    hasta = serializers.DateField(read_only=True)
    dias = serializers.ListField(child=serializers.DateField(), read_only=True)
    # CharField para no crear un enum nuevo en el esquema (ya existe EstadoSolicitud)
    estados_solicitud_incluidos = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="Valores posibles: PEND, APROB, RECH, CANC",
    )
    items = CalendarioEmpleadoRowSerializer(many=True, read_only=True)

    class Meta:
        ref_name = "CalendarioResponse"
