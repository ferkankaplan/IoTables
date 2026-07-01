from fastapi.testclient import TestClient

from iotables.main import create_app


def test_health_live_returns_safe_status() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "IoTables",
        "environment": "local",
    }
