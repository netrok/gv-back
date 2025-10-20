from rest_framework import serializers
from .models import UnidadNegocio, Sucursal, Area, Ubicacion


class UnidadNegocioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadNegocio
        fields = "__all__"


class SucursalSerializer(serializers.ModelSerializer):
    unidad_nombre = serializers.CharField(source="unidad.nombre", read_only=True)

    class Meta:
        model = Sucursal
        fields = "__all__"


class AreaSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    parent_nombre = serializers.CharField(source="parent.nombre", read_only=True)

    class Meta:
        model = Area
        fields = "__all__"


class UbicacionSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    area_nombre = serializers.CharField(source="area.nombre", read_only=True)

    class Meta:
        model = Ubicacion
        fields = "__all__"

    def validate(self, attrs):
        suc = attrs.get("sucursal") or getattr(self.instance, "sucursal", None)
        area = attrs.get("area") or getattr(self.instance, "area", None)
        if not suc and not area:
            raise serializers.ValidationError("Debe indicar 'sucursal' o 'area'.")
        return attrs
