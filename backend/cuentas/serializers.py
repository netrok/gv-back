from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserMeSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email",
            "is_active", "is_staff", "is_superuser", "groups",
        ]


class PermissionSerializer(serializers.Serializer):
    permissions = serializers.ListField(
        child=serializers.CharField(), help_text="Lista app.codename"
    )
