from datetime import UTC, datetime

from fastapi.testclient import TestClient

from iotables.api.table_display import get_table_display_presence_service
from iotables.main import create_app
from iotables.modules.ordering.table_presence import QrTokenPayload


class FakeTablePresenceService:
    def __init__(self) -> None:
        self.display_credential: str | None = None

    async def issue_current_qr_token(self, *, display_credential: str) -> QrTokenPayload:
        self.display_credential = display_credential
        return QrTokenPayload(
            qr_token="raw-qr-token",
            expires_at=datetime(2026, 7, 3, 12, 1, tzinfo=UTC),
            refresh_after_seconds=60,
        )


def make_client(service: FakeTablePresenceService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_table_display_presence_service] = lambda: service
    return TestClient(app)


def test_table_display_qr_token_requires_display_credential_scheme() -> None:
    service = FakeTablePresenceService()
    client = make_client(service)

    missing = client.get("/api/table-display/qr-token")
    wrong_scheme = client.get(
        "/api/table-display/qr-token",
        headers={"Authorization": "Bearer abc"},
    )
    response = client.get(
        "/api/table-display/qr-token",
        headers={"Authorization": "DisplayCredential display-secret"},
    )

    assert missing.status_code == 401
    assert wrong_scheme.status_code == 401
    assert response.status_code == 200
    assert response.json()["qrToken"] == "raw-qr-token"
    assert response.json()["refreshAfterSeconds"] == 60
    assert service.display_credential == "display-secret"
