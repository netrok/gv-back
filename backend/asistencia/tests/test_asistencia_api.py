import json
import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from asistencia.tests.factories import (
    UserFactory, EmpleadoFactory, UbicacionFactory
)

# --- Helpers ---------------------------------------------------------------

def jwt_login(client: APIClient, username: str, password: str) -> str:
    resp = client.post(
        "/api/auth/token/",
        {"username": username, "password": password},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    return resp.json()["access"]


# --- Tests -----------------------------------------------------------------

@pytest.mark.django_db
def test_schema_ok(client):
    resp = client.get("/api/schema/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_list_checadas_requires_auth():
    c = APIClient()
    resp = c.get("/api/v1/asistencia/checadas/")
    # según permisos configurados, puede ser 401 (no auth) o 403 (auth sin permiso)
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_create_checada_as_rrhh():
    # Arrange: usuario con rol RRHH
    user = UserFactory()
    rrhh, _ = Group.objects.get_or_create(name="RRHH")
    user.groups.add(rrhh)
    user.set_password("pass123")
    user.save()

    c = APIClient()
    access = jwt_login(c, user.username, "pass123")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    emp = EmpleadoFactory()
    ubi = UbicacionFactory()

    payload = {
        "empleado": emp.id,
        "tipo": "IN",
        "fuente": "WEB",
        "ubicacion_id": ubi.id,
        "nota": "prueba",
    }

    # Act
    resp = c.post(
        "/api/v1/asistencia/checadas/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    # Assert
    assert resp.status_code in (200, 201), resp.content
    data = resp.json()
    assert data["empleado"] == emp.id
    assert data["tipo"] == "IN"


@pytest.mark.django_db
def test_normal_user_cannot_create_checada():
    # Arrange: usuario sin rol
    user = UserFactory()
    user.set_password("pass123")
    user.save()

    c = APIClient()
    access = jwt_login(c, user.username, "pass123")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    emp = EmpleadoFactory()

    # Act
    resp = c.post(
        "/api/v1/asistencia/checadas/",
        {"empleado": emp.id, "tipo": "IN", "fuente": "WEB"},
        format="json",
    )

    # Assert
    assert resp.status_code in (403, 401), resp.content
