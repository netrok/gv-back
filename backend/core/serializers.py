# backend/core/serializers.py
from rest_framework import serializers

class HealthSerializer(serializers.Serializer):
    status = serializers.CharField(read_only=True)
    app = serializers.CharField(read_only=True)
