from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.auth import get_identity_access_service
from iotables.main import create_app
from iotables.modules.access.identity import LoginResult
from iotables.security.context import ActorContext, ActorType, AppScope

USER_ID = UUID("22222222-2222-2222-2222-222222222222")
SESSION_ID = UUID("33333333-3333-3333-3333-333333333333")


class FakeIdentityAccessService:
    def __init__(self) -> None:
        self.login_username: str | None = None
        self.login_password: str | None = None
        self.logged_out_session_id: UUID | None = None

    async def get_login_requirements(
        self,
        *,
        app_scope: AppScope,
        username: str,
    ) -> dict[str, object]:
        return {
            "status": "password_required",
            "totpRequired": app_scope == AppScope.PLATFORM and username == "owner",
            "firstPasswordRequired": False,
        }

    async def authenticate_platform(
        self,
        *,
        username: str,
        password: str,
        totp_code: str | None = None,
    ) -> LoginResult:
        _ = totp_code
        self.login_username = username
        self.login_password = password
        return LoginResult(
            status="authenticated",
            actor=platform_actor(),
            session_token="raw-session-token",
            expires_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        )

    async def logout(self, *, session_id: UUID) -> None:
        self.logged_out_session_id = session_id


class FakeSessionResolver:
    async def resolve(self, session_token: str) -> ActorContext | None:
        if session_token == "raw-session-token":
            return platform_actor()
        return None


def platform_actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.PLATFORM_OWNER,
        app_scope=AppScope.PLATFORM,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


def make_client(service: FakeIdentityAccessService) -> TestClient:
    app = create_app()
    app.state.session_resolver = FakeSessionResolver()
    app.dependency_overrides[get_identity_access_service] = lambda: service
    return TestClient(app)


def test_login_requirements_use_app_scope_query_alias() -> None:
    service = FakeIdentityAccessService()
    client = make_client(service)

    response = client.get("/api/v1/auth/login-requirements?appScope=platform&username=owner")

    assert response.status_code == 200
    assert response.json() == {
        "status": "password_required",
        "totpRequired": True,
        "firstPasswordRequired": False,
    }


def test_platform_login_sets_http_only_session_cookie() -> None:
    service = FakeIdentityAccessService()
    client = make_client(service)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "appScope": "platform",
            "username": "Owner",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "authenticated"
    assert response.json()["actor"]["appScope"] == "platform"
    assert "iotables_session=raw-session-token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert service.login_username == "owner"
    assert service.login_password == "secret"


def test_session_returns_current_actor_from_cookie() -> None:
    client = make_client(FakeIdentityAccessService())
    client.cookies.set("iotables_session", "raw-session-token")

    response = client.get("/api/v1/auth/session")

    assert response.status_code == 200
    assert response.json()["actor"]["userId"] == str(USER_ID)
    assert response.json()["actor"]["appScope"] == "platform"


def test_logout_requires_csrf_token() -> None:
    client = make_client(FakeIdentityAccessService())
    client.cookies.set("iotables_session", "raw-session-token")

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_required"


def test_logout_revokes_current_session_and_clears_cookie() -> None:
    service = FakeIdentityAccessService()
    client = make_client(service)
    client.cookies.set("iotables_session", "raw-session-token")

    response = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": "csrf"})

    assert response.status_code == 200
    assert response.json() == {"status": "logged_out"}
    assert service.logged_out_session_id == SESSION_ID
    assert "iotables_session=" in response.headers["set-cookie"]
