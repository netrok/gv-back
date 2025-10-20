from rest_framework import serializers
from .models import PoliticaVacaciones, Feriado, BalanceVacaciones, SolicitudVacaciones
from .utils import dias_habiles


# =========================
# Básicos
# =========================
class PoliticaVacacionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoliticaVacaciones
        fields = "__all__"


class FeriadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feriado
        fields = "__all__"


class BalanceVacacionesSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)

    class Meta:
        model = BalanceVacaciones
        fields = "__all__"
        read_only_fields = ("actualizado_en", "empleado_nombre")


# =========================
# Solicitudes (lectura/edición)
# =========================
class SolicitudVacacionesSerializer(serializers.ModelSerializer):
    # Extras de salida
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)
    # Mostrar etiqueta legible si existe get_estado_display
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = SolicitudVacaciones
        fields = "__all__"
        # listamos todos los posibles read-only, pero los que no existan en el modelo
        # los filtramos dinámicamente en __init__ para evitar errores.
        read_only_fields = (
            # timestamps y sistema
            "creado_por", "creado_en", "actualizado_en",
            # estado y resolución (v2)
            "estado", "resuelto_por", "resuelto_en",
            # legacy de aprobación (si existieran en tu modelo actual)
            "aprobado_por", "aprobado_en", "comentario_aprobador",
            # cálculo de días (según el campo real del modelo)
            "dias_habiles", "empleado_nombre", "estado_display",
        )

    def __init__(self, *args, **kwargs):
        """
        Quita de read_only_fields los campos que no existan realmente,
        para soportar modelos legacy (con 'dias') o nuevos (con 'dias_habiles'),
        y con/sin campos de aprobación.
        """
        super().__init__(*args, **kwargs)
        # Filtrar read_only_fields inexistentes
        if hasattr(self.Meta, "read_only_fields"):
            ro = list(self.Meta.read_only_fields)
            ro = [f for f in ro if f in self.fields]
            self.Meta.read_only_fields = tuple(ro)

    # ---------- Validaciones de negocio mínimas ----------
    def validate(self, attrs):
        """
        - Valida rango de fechas.
        - Calcula días hábiles y lo coloca en el campo correcto:
          'dias_habiles' si existe, de lo contrario 'dias' (legacy).
        """
        fi = attrs.get("fecha_inicio") or getattr(self.instance, "fecha_inicio", None)
        ff = attrs.get("fecha_fin") or getattr(self.instance, "fecha_fin", None)

        if not fi or not ff:
            raise serializers.ValidationError("Debes proporcionar fecha_inicio y fecha_fin.")
        if ff < fi:
            raise serializers.ValidationError("fecha_fin debe ser mayor o igual a fecha_inicio.")

        # Calcula días hábiles (utilidad actual: excluye fines y feriados globales)
        dh = dias_habiles(fi, ff)

        # Colocar el resultado en el campo existente
        if "dias_habiles" in self.fields:
            attrs["dias_habiles"] = dh
        elif "dias" in self.fields:
            attrs["dias"] = dh
        # si ninguno existe, lo dejamos solo como validación de rango

        return attrs

    # ---------- Crear / Actualizar ----------
    def create(self, validated_data):
        """
        Si el modelo implementa guardar_con_calculo(), úsalo.
        Sino, usamos el cálculo ya inyectado por validate().
        """
        obj = SolicitudVacaciones(**validated_data)
        if hasattr(obj, "guardar_con_calculo"):
            obj.guardar_con_calculo()
            return obj
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Al actualizar fechas, recalcula días (ya lo hicimos en validate()).
        Si existe guardar_con_calculo(), úsalo para mantener consistencia.
        """
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if hasattr(instance, "guardar_con_calculo"):
            instance.guardar_con_calculo()
            return instance
        instance.save()
        return instance


# =========================
# Solicitudes (creación)
# =========================
class SolicitudVacacionesCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de creación simple.
    Deja que el modelo calcule 'dias_habiles' (o 'dias') con guardar_con_calculo().
    """
    class Meta:
        model = SolicitudVacaciones
        # Campos mínimos típicos (ajusta si tu modelo requiere otros)
        fields = ("empleado", "fecha_inicio", "fecha_fin", "comentario")

    def validate(self, attrs):
        fi = attrs.get("fecha_inicio")
        ff = attrs.get("fecha_fin")
        if not fi or not ff:
            raise serializers.ValidationError("Debes proporcionar fecha_inicio y fecha_fin.")
        if ff < fi:
            raise serializers.ValidationError("fecha_fin debe ser mayor o igual a fecha_inicio.")
        return attrs

    def create(self, validated_data):
        obj = SolicitudVacaciones(**validated_data)
        if hasattr(obj, "guardar_con_calculo"):
            obj.guardar_con_calculo()
            return obj
        # Fallback (si no hay método en el modelo):
        # calcula y asigna al campo correcto.
        dh = dias_habiles(validated_data["fecha_inicio"], validated_data["fecha_fin"])
        if hasattr(obj, "dias_habiles"):
            obj.dias_habiles = dh
        elif hasattr(obj, "dias"):
            obj.dias = dh
        obj.save()
        return obj
