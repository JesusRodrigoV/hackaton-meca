from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token


def test_api_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "MECA API is running"


def test_healthz():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unauthorized_access_protected_route():
    client = TestClient(app)
    response = client.get("/api/v1/presupuestos/techos")
    assert response.status_code in (401, 403)


def test_get_modificaciones_authenticated():
    client = TestClient(app)
    token = create_access_token(subject=1)
    response = client.get(
        "/api/v1/presupuestos/modificaciones",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
