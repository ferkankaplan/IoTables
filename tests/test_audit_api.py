from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.audit import get_audit_query_service
from iotables.main import create_app
from iotables.modules.governance.audit import AuditEvent
from iotables.security.context import ActorContext, ActorType, AppScope

PLATFORM_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
TENANT_ID = UUID("33333333-3333-3333-3333-333333333333")
AUDIT_EVENT_ID = UUID("55555555-5555-5555-5555-555555555555")


class FakeSessionResolver:
    def __init__(self, actor: ActorContext | None) -> None:
        self.actor = actor

    async def resolve(self, session_token: str) -> ActorContext | None:
        return self.actor if session_token == "session-token" else None


class FakeAuditQueryService:
    def __init__(self) -> None:
        self.query_args: dict[str, object] | None = None

    async def query_platform_audit(
        self,
        *,
        tenant_id: UUID | None,
        action: str | None,
        from_at: datetime | None,
        to_at: datetime | None,
        cursor: int,
        limit: int,
    ) -> tuple[list[AuditEvent], int | None]:
        self.query_args = {
            "tenant_id": tenant_id,
            "action": action,
            "from_at": from_at,
            "to_at": to_at,
            "cursor": cursor,
            "limit": limit,
        }
        return (
            [
                AuditEvent(
                    audit_event_id=AUDIT_EVENT_ID,
                    tenant_id=tenant_id,
                    actor_user_id=PLATFORM_USER_ID,
                    action=action or "tenant.profile_updated",
                    target_type="tenant",
                    target_id=str(tenant_id),
                    reason="manual update",
                    metadata={"changedFields": ["capacity"]},
                    created_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
                )
            ],
            125,
        )


def make_platform_actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.PLATFORM_OWNER,
        app_scope=AppScope.PLATFORM,
        user_id=PLATFORM_USER_ID,
    )


def make_client(
    *,
    actor: ActorContext | None,
    service: FakeAuditQueryService | None = None,
) -> TestClient:
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(actor)
    if service is not None:
        app.dependency_overrides[get_audit_query_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "session-token")
    return client


def test_query_platform_audit_events_returns_redacted_timeline() -> None:
    service = FakeAuditQueryService()
    client = make_client(actor=make_platform_actor(), service=service)

    response = client.get(
        "/api/platform/audit-events"
        f"?tenantId={TENANT_ID}"
        "&action=tenant.profile_updated"
        "&from=2026-07-03T08:00:00%2B00:00"
        "&to=2026-07-03T10:00:00%2B00:00"
        "&cursor=25"
        "&limit=250"
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "auditEventId": str(AUDIT_EVENT_ID),
                "tenantId": str(TENANT_ID),
                "actor": {"userId": str(PLATFORM_USER_ID)},
                "action": "tenant.profile_updated",
                "target": {"type": "tenant", "id": str(TENANT_ID)},
                "reason": "manual update",
                "metadata": {"changedFields": ["capacity"]},
                "createdAt": "2026-07-03T09:00:00+00:00",
            }
        ],
        "page": {"nextCursor": "125", "limit": 100},
    }
    assert service.query_args == {
        "tenant_id": TENANT_ID,
        "action": "tenant.profile_updated",
        "from_at": datetime(2026, 7, 3, 8, 0, tzinfo=UTC),
        "to_at": datetime(2026, 7, 3, 10, 0, tzinfo=UTC),
        "cursor": 25,
        "limit": 100,
    }


def test_query_platform_audit_events_requires_platform_session() -> None:
    client = make_client(actor=None, service=FakeAuditQueryService())

    response = client.get("/api/platform/audit-events")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
