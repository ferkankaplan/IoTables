from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.tenant import get_tenant_registry_query_service_for_tenant
from iotables.main import create_app
from iotables.modules.platform.provisioning import TenantContext, TenantProfile
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole

TENANT_ID = UUID("33333333-3333-3333-3333-333333333333")
USER_ID = UUID("44444444-4444-4444-4444-444444444444")


class FakeSessionResolver:
    def __init__(self, actor: ActorContext | None) -> None:
        self.actor = actor

    async def resolve(self, session_token: str) -> ActorContext | None:
        if session_token == "valid":
            return self.actor
        return None


class FakeTenantRegistryQueryService:
    def __init__(self) -> None:
        self.subdomain: str | None = None
        self.profile_tenant_id: UUID | None = None

    async def resolve_by_subdomain(self, subdomain: str) -> TenantContext:
        self.subdomain = subdomain
        return TenantContext(
            tenant_id=TENANT_ID,
            name="Cafe Demo",
            subdomain=subdomain,
            status="active",
            sector="cafe",
            capacity=24,
            address="Kadikoy",
        )

    async def get_tenant_profile(self, tenant_id: UUID) -> TenantProfile:
        self.profile_tenant_id = tenant_id
        now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
        return TenantProfile(
            tenant_id=tenant_id,
            name="Cafe Demo",
            subdomain="demo-cafe",
            gsm_number="+905551112233",
            sector="cafe",
            capacity=24,
            address="Kadikoy",
            status="active",
            provisioning_state="ready",
            starter_template_state="applied",
            tenant_admin_bootstrap_state="completed",
            health_flags=(),
            created_at=now,
            updated_at=now,
        )


def make_actor(
    *,
    app_scope: AppScope = AppScope.TENANT,
    roles: frozenset[StaffRole] = frozenset({StaffRole.TENANT_ADMIN}),
) -> ActorContext:
    return ActorContext(
        actor_type=ActorType.TENANT_USER,
        app_scope=app_scope,
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        roles=roles,
    )


def make_client(
    *,
    actor: ActorContext | None = None,
    service: FakeTenantRegistryQueryService | None = None,
    tenant_root_domains: list[str] | None = None,
) -> TestClient:
    app = create_app()
    if tenant_root_domains is not None:
        app.state.settings.tenant_root_domains = tenant_root_domains
    app.state.session_resolver = FakeSessionResolver(actor)
    if service is not None:
        app.dependency_overrides[get_tenant_registry_query_service_for_tenant] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "valid")
    return client


def test_tenant_context_resolves_from_local_tenant_header() -> None:
    service = FakeTenantRegistryQueryService()
    client = make_client(service=service)

    response = client.get("/api/tenant/context", headers={"X-Tenant-Subdomain": "demo-cafe"})

    assert response.status_code == 200
    assert response.json()["tenantId"] == str(TENANT_ID)
    assert response.json()["subdomain"] == "demo-cafe"
    assert service.subdomain == "demo-cafe"


def test_tenant_context_resolves_from_production_host() -> None:
    service = FakeTenantRegistryQueryService()
    client = make_client(service=service)

    response = client.get("/api/tenant/context", headers={"Host": "demo-cafe.iotables.net"})

    assert response.status_code == 200
    assert response.json()["subdomain"] == "demo-cafe"
    assert service.subdomain == "demo-cafe"


def test_tenant_context_resolves_from_configured_staging_host() -> None:
    service = FakeTenantRegistryQueryService()
    client = make_client(service=service, tenant_root_domains=["iotables.net", "tabflow.uk"])

    response = client.get("/api/tenant/context", headers={"Host": "demo-cafe.tabflow.uk"})

    assert response.status_code == 200
    assert response.json()["subdomain"] == "demo-cafe"
    assert service.subdomain == "demo-cafe"


def test_tenant_context_ignores_platform_host() -> None:
    service = FakeTenantRegistryQueryService()
    client = make_client(service=service, tenant_root_domains=["iotables.net", "tabflow.uk"])

    response = client.get("/api/tenant/context", headers={"Host": "platform.tabflow.uk"})

    assert response.status_code == 404
    assert service.subdomain is None


def test_tenant_profile_requires_session() -> None:
    client = make_client(actor=None, service=FakeTenantRegistryQueryService())

    response = client.get("/api/tenant/profile")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_tenant_profile_rejects_non_tenant_admin_role() -> None:
    client = make_client(
        actor=make_actor(roles=frozenset({StaffRole.CASHIER})),
        service=FakeTenantRegistryQueryService(),
    )

    response = client.get("/api/tenant/profile")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_authorized"


def test_tenant_profile_uses_actor_tenant_scope() -> None:
    service = FakeTenantRegistryQueryService()
    client = make_client(actor=make_actor(), service=service)

    response = client.get("/api/tenant/profile")

    assert response.status_code == 200
    assert response.json()["tenantId"] == str(TENANT_ID)
    assert response.json()["name"] == "Cafe Demo"
    assert service.profile_tenant_id == TENANT_ID
