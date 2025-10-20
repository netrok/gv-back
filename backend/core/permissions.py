# core/permissions.py
from typing import Iterable
from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_has_role(user, roles: Iterable[str]) -> bool:
    """
    True si el usuario (auth) tiene alguno de los roles indicados.
    - Superuser: siempre True.
    - Staff: se considera como 'ADMIN' (puedes quitarlo si no lo quieres así).
    - Grupos de Django: se comparan por nombre, case-insensitive.
    """
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True

    normalized = {r.upper() for r in roles}

    # Opcional: contar staff como ADMIN
    if user.is_staff and ("ADMIN" in normalized):
        return True

    group_names = set(
        name.upper() for name in user.groups.values_list("name", flat=True)
    )
    return bool(normalized & group_names)


class IsAuthenticatedReadOnlyOrRRHH(BasePermission):
    """
    - GET/HEAD/OPTIONS: requiere estar autenticado.
    - POST/PUT/PATCH/DELETE: requiere rol en {RRHH, ADMIN, SUPERADMIN, SUPERVISOR, GERENTE}.
    """

    WRITE_ROLES = ("RRHH", "Admin", "SuperAdmin", "Supervisor", "Gerente")

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if request.method in SAFE_METHODS:
            return bool(user and user.is_authenticated)
        return user_has_role(user, self.WRITE_ROLES)

    def has_object_permission(self, request, view, obj):
        # misma lógica a nivel de objeto
        return self.has_permission(request, view)


class IsRRHHEditOnly(BasePermission):
    """
    - GET/HEAD/OPTIONS: requiere estar autenticado.
    - POST/PUT/PATCH/DELETE: sólo {RRHH, ADMIN, SUPERADMIN}.
    """

    WRITE_ROLES = ("RRHH", "Admin", "SuperAdmin")

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if request.method in SAFE_METHODS:
            return bool(user and user.is_authenticated)
        return user_has_role(user, self.WRITE_ROLES)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
