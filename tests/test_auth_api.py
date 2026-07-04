from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.auth import get_identity_access_service
from iotables.main import create_app
from iotables.modules.access.identity import FirstPasswordSetupState, LoginResult
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole

USER_ID = UUID("22222222-2222-2222-2222-222222222222")
SESSION_ID = UUID("33333333-3333-3333-3333-333333333333")
OTP_CHALLENGE_ID = UUID("55555555-5555-5555-5555-555555555555")


class FakeIdentityAccessService:
    def __init__(self) -> None:
        self.login_username: str | None = None
        self.login_password: str | None = None
        self.login_app_scope: AppScope | None = None
        self.login_tenant_subdomain: str | None = None
        self.logged_out_session_id: UUID | None = None

    async def get_login_requirements(
        self,
        *,
        app_scope: AppScope,
        username: str,
        tenant_subdomain: str | None = None,
    ) -> dict[str, object]:
        _ = tenant_subdomain
        return {
            "status": "password_required",
            "totpRequired": app_scope == AppScope.PLATFORM and username == "owner",
            "firstPasswordRequired": app_scope == AppScope.TENANT and username == "demo",
        }

    async def authenticate(
        self,
        *,
        app_scope: AppScope,
        username: str,
        password: str,
        tenant_subdomain: str | None = None,
        totp_code: str | None = None,
    ) -> LoginResult:
        _ = totp_code
        self.login_app_scope = app_scope
        self.login_username = username
        self.login_password = password
        self.login_tenant_subdomain = tenant_subdomain
        return LoginResult(
            status="authenticated",
            actor=platform_actor() if app_scope == AppScope.PLATFORM else tenant_actor(),
            session_token="raw-session-token",
            expires_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        )

    async def begin_first_password_setup(self, *, setup_token: str) -> FirstPasswordSetupState:
        assert setup_token == "setup-token"
        return FirstPasswordSetupState(
            status="otp_required",
            setup_token=setup_token,
            otp_required=True,
            otp_challenge_id=OTP_CHALLENGE_ID,
            target_hint="*******1234",
            expires_at=datetime(2026, 7, 2, 11, 5, tzinfo=UTC),
            remaining_attempts=5,
        )

    async def complete_first_password_setup(
        self,
        *,
        setup_token: str,
        new_password: str,
        otp_challenge_id: UUID | None = None,
        otp_code: str | None = None,
    ) -> LoginResult:
        assert setup_token == "setup-token"
        assert new_password == "new-secret"
        assert otp_challenge_id == OTP_CHALLENGE_ID
        assert otp_code == "123456"
        return LoginResult(
            status="authenticated",
            actor=tenant_actor(),
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


def tenant_actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.TENANT_USER,
        app_scope=AppScope.TENANT,
        user_id=USER_ID,
        tenant_id=UUID("44444444-4444-4444-4444-444444444444"),
        roles=frozenset({StaffRole.TENANT_ADMIN}),
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
    assert service.login_app_scope == AppScope.PLATFORM
    assert service.login_username == "owner"
    assert service.login_password == "secret"
    assert service.login_tenant_subdomain is None


def test_tenant_login_passes_header_tenant_context_to_identity_service() -> None:
    service = FakeIdentityAccessService()
    client = make_client(service)

    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-Subdomain": "demo-cafe"},
        json={
            "appScope": "tenant",
            "username": "Demo",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "authenticated"
    assert response.json()["actor"]["appScope"] == "tenant"
    assert response.json()["actor"]["tenantId"] == "44444444-4444-4444-4444-444444444444"
    assert response.json()["actor"]["roles"] == ["tenant_admin"]
    assert service.login_app_scope == AppScope.TENANT
    assert service.login_username == "demo"
    assert service.login_password == "secret"
    assert service.login_tenant_subdomain == "demo-cafe"


def test_first_password_begin_returns_redacted_otp_setup_state() -> None:
    service = FakeIdentityAccessService()
    client = make_client(service)

    response = client.post(
        "/api/v1/auth/first-password/begin",
        json={"setupToken": "setup-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "otp_required",
        "setupToken": "setup-token",
        "otpRequired": True,
        "otpChallengeId": str(OTP_CHALLENGE_ID),
        "targetHint": "*******1234",
        "expiresAt": "2026-07-02T11:05:00+00:00",
        "remainingAttempts": 5,
    }
    assert "123456" not in response.text


def test_first_password_complete_sets_session_cookie() -> None:
    service = FakeIdentityAccessService()
    client = make_client(service)

    response = client.post(
        "/api/v1/auth/first-password/complete",
        json={
            "setupToken": "setup-token",
            "newPassword": "new-secret",
            "otpChallengeId": str(OTP_CHALLENGE_ID),
            "otpCode": "123456",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "authenticated"
    assert response.json()["actor"]["appScope"] == "tenant"
    assert "iotables_session=raw-session-token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


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
