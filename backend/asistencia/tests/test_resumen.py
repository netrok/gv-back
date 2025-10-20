import pytest
from rest_framework.test import APIClient
from .factories import UserFactory, EmpleadoFactory, ChecadaFactory

@pytest.mark.django_db
def test_resumen_requires_auth():
    c = APIClient()
    resp = c.get("/api/v1/asistencia/resumen/?fecha_desde=2025-01-01&fecha_hasta=2025-01-31")
    assert resp.status_code in (401, 403)

@pytest.mark.django_db
def test_resumen_ok_jwt():
    # Usuario normal autenticado
    user = UserFactory()
    user.set_password("pass123")
    user.save()

    c = APIClient()
    token_resp = c.post(
        "/api/auth/token/",
        {"username": user.username, "password": "pass123"},
        format="json",
    )
    assert token_resp.status_code == 200, token_resp.content
    access = token_resp.json().get("access")
    assert access, token_resp.content
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    # Datos: dos checadas mismo día (IN / OUT)
    emp = EmpleadoFactory()
    ch_in = ChecadaFactory(empleado=emp, tipo="IN")
    ch_out = ChecadaFactory(empleado=emp, tipo="OUT")
    fd = ch_in.ts.date().isoformat()
    fh = fd

    resp = c.get(f"/api/v1/asistencia/resumen/?fecha_desde={fd}&fecha_hasta={fh}&empleado={emp.id}")
    assert resp.status_code == 200, resp.content
    data = resp.json()
    assert isinstance(data, list) and len(data) >= 1
    # Debe existir la primera entrada
    assert data[0].get("primera_entrada") is not None
