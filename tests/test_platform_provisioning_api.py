from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.platform import (
    get_tenant_provisioning_service,
    get_tenant_registry_mutation_service,
    get_tenant_registry_query_service,
)
from iotables.main import create_app
from iotables.modules.platform.provisioning import (
    CreateTenantCommand,
    ProvisioningRecoverySummary,
    ProvisioningResult,
    ProvisioningState,
    TenantHealthSummary,
    TenantLifecycleEvent,
    TenantProfile,
    TenantProfileUpdateCommand,
)
from iotables.security.context import ActorContext, ActorType, AppScope

PLATFORM_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
TENANT_ID = UUID("33333333-3333-3333-3333-333333333333")


class FakeSessionResolver:
    def __init__(self, actor: ActorContext | None) -> None:
        self.actor = actor

    async def resolve(self, session_token: str) -> ActorContext | None:
        if session_token == "valid":
            return self.actor
        return None


class FakeProvisioningService:
    def __init__(self) -> None:
        self.actor: ActorContext | None = None
        self.command: CreateTenantCommand | None = None
        self.idempotency_key: str | None = None
        self.state_tenant_id: UUID | None = None
        self.summary_tenant_id: UUID | None = None
        self.retry_args: dict[str, object] | None = None
        self.recovery_needed_args: dict[str, object] | None = None

    async def start_tenant(
        self,
        *,
        actor: ActorContext,
        command: CreateTenantCommand,
        idempotency_key: str,
    ) -> ProvisioningResult:
        self.actor = actor
        self.command = command
        self.idempotency_key = idempotency_key
        return ProvisioningResult(
            tenant_id=TENANT_ID,
            status="active",
            subdomain=command.subdomain,
            starter_template_applied=command.sector == "cafe",
            failure_summary=None,
            dns_ready=False,
        )

    async def get_state(self, tenant_id: UUID) -> ProvisioningState:
        self.state_tenant_id = tenant_id
        return make_provisioning_state(tenant_id=tenant_id)

    async def get_recovery_summary(self, tenant_id: UUID) -> ProvisioningRecoverySummary:
        self.summary_tenant_id = tenant_id
        return ProvisioningRecoverySummary(
            tenant_id=tenant_id,
            missing_required_records=("halls", "stations"),
            completed_phases=("tenant_admin_user",),
            failed_phase="starter_template",
            safe_retry_allowed=True,
            failure_summary="starter template failed",
        )

    async def retry_failed(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        recovery_note: str | None,
    ) -> ProvisioningState:
        self.retry_args = {"actor": actor, "tenant_id": tenant_id, "recovery_note": recovery_note}
        return make_provisioning_state(tenant_id=tenant_id, tenant_status="active")

    async def mark_recovery_needed(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        reason: str,
    ) -> ProvisioningState:
        self.recovery_needed_args = {"actor": actor, "tenant_id": tenant_id, "reason": reason}
        return make_provisioning_state(
            tenant_id=tenant_id,
            tenant_status="provisioning_failed",
            starter_application_status="recovery_needed",
            failure_summary=reason,
        )


def make_provisioning_state(
    *,
    tenant_id: UUID,
    tenant_status: str = "provisioning_failed",
    starter_application_status: str = "failed",
    failure_summary: str | None = "starter template failed",
) -> ProvisioningState:
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    return ProvisioningState(
        tenant_id=tenant_id,
        tenant_status=tenant_status,
        starter_application_status=starter_application_status,
        template_key="cafe_default",
        template_version=1,
        failure_summary=failure_summary,
        dns_ready=False,
        created_at=now,
        updated_at=now,
    )


class FakeTenantRegistryQueryService:
    def __init__(self) -> None:
        self.list_args: dict[str, object] | None = None
        self.detail_tenant_id: UUID | None = None
        self.lifecycle_args: dict[str, object] | None = None

    async def list_tenants(
        self,
        *,
        status: str | None = None,
        sector: str | None = None,
        q: str | None = None,
        cursor: int = 0,
        limit: int = 50,
    ) -> tuple[list[TenantHealthSummary], int | None]:
        self.list_args = {
            "status": status,
            "sector": sector,
            "q": q,
            "cursor": cursor,
            "limit": limit,
        }
        now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
        return (
            [
                TenantHealthSummary(
                    tenant_id=TENANT_ID,
                    name="Cafe Demo",
                    subdomain="demo-cafe",
                    status="active",
                    dns_ready=False,
                    sector="cafe",
                    provisioning_state="ready",
                    last_lifecycle_event_at=now,
                    health_flags=("dns_not_ready",),
                    created_at=now,
                    updated_at=now,
                )
            ],
            50,
        )

    async def get_tenant_profile(self, tenant_id: UUID) -> TenantProfile:
        self.detail_tenant_id = tenant_id
        now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
        return TenantProfile(
            tenant_id=tenant_id,
            name="Cafe Demo",
            subdomain="demo-cafe",
            gsm_number="+905551112233",
            sector="cafe",
            capacity=24,
            address='{"city":"Istanbul"}',
            status="active",
            dns_ready=False,
            provisioning_state="ready",
            starter_template_state="applied",
            tenant_admin_bootstrap_state="first_password_required",
            health_flags=("dns_not_ready",),
            created_at=now,
            updated_at=now,
        )

    async def list_lifecycle_events(
        self, *, tenant_id: UUID, cursor: int, limit: int
    ) -> tuple[list[TenantLifecycleEvent], int | None]:
        self.lifecycle_args = {"tenant_id": tenant_id, "cursor": cursor, "limit": limit}
        now = datetime(2026, 7, 2, 12, 5, tzinfo=UTC)
        return (
            [
                TenantLifecycleEvent(
                    event_id=UUID("44444444-4444-4444-4444-444444444444"),
                    tenant_id=tenant_id,
                    previous_status="active",
                    next_status="suspended",
                    actor_user_id=PLATFORM_USER_ID,
                    reason="manual maintenance",
                    created_at=now,
                )
            ],
            50,
        )


class FakeTenantRegistryMutationService:
    def __init__(self) -> None:
        self.profile_args: dict[str, object] | None = None
        self.dns_args: dict[str, object] | None = None
        self.status_args: dict[str, object] | None = None

    async def update_profile(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        command: TenantProfileUpdateCommand,
    ) -> TenantProfile:
        self.profile_args = {"actor": actor, "tenant_id": tenant_id, "command": command}
        return make_profile(
            tenant_id=tenant_id,
            gsm_number=command.fields.get("gsm_number") or "+905551112233",
            capacity=command.fields.get("capacity"),
            address=command.fields.get("address"),
        )

    async def set_dns_ready(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        dns_ready: bool,
    ) -> TenantProfile:
        self.dns_args = {"actor": actor, "tenant_id": tenant_id, "dns_ready": dns_ready}
        return make_profile(tenant_id=tenant_id, dns_ready=dns_ready)

    async def change_status(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        next_status: str,
        reason: str,
    ) -> TenantProfile:
        self.status_args = {
            "actor": actor,
            "tenant_id": tenant_id,
            "next_status": next_status,
            "reason": reason,
        }
        return make_profile(tenant_id=tenant_id, status=next_status)


def make_profile(
    *,
    tenant_id: UUID,
    gsm_number: str = "+905551112233",
    capacity: int | None = 24,
    address: str | None = '{"city":"Istanbul"}',
    status: str = "active",
    dns_ready: bool = False,
) -> TenantProfile:
    now = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    return TenantProfile(
        tenant_id=tenant_id,
        name="Cafe Demo",
        subdomain="demo-cafe",
        gsm_number=gsm_number,
        sector="cafe",
        capacity=capacity,
        address=address,
        status=status,
        dns_ready=dns_ready,
        provisioning_state="ready",
        starter_template_state="applied",
        tenant_admin_bootstrap_state="first_password_required",
        health_flags=("dns_not_ready",) if not dns_ready else (),
        created_at=now,
        updated_at=now,
    )


def make_platform_actor(app_scope: AppScope = AppScope.PLATFORM) -> ActorContext:
    return ActorContext(
        actor_type=ActorType.PLATFORM_OWNER,
        app_scope=app_scope,
        user_id=PLATFORM_USER_ID,
    )


def make_client(
    *,
    actor: ActorContext | None = None,
    service: FakeProvisioningService | None = None,
    query_service: FakeTenantRegistryQueryService | None = None,
    mutation_service: FakeTenantRegistryMutationService | None = None,
) -> TestClient:
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(actor)
    if service is not None:
        app.dependency_overrides[get_tenant_provisioning_service] = lambda: service
    if query_service is not None:
        app.dependency_overrides[get_tenant_registry_query_service] = lambda: query_service
    if mutation_service is not None:
        app.dependency_overrides[get_tenant_registry_mutation_service] = lambda: mutation_service
    client = TestClient(app)
    client.cookies.set("iotables_session", "valid")
    return client


def test_create_tenant_requires_platform_session() -> None:
    client = make_client(actor=None, service=FakeProvisioningService())

    response = client.post(
        "/api/platform/tenants",
        headers={
            "X-Request-Id": "req_platform_auth",
            "X-CSRF-Token": "csrf",
            "Idempotency-Key": "tenant-create-1",
        },
        json={
            "name": "Cafe Demo",
            "subdomain": "demo-cafe",
            "gsmNumber": "+905551112233",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_create_tenant_rejects_wrong_app_scope() -> None:
    client = make_client(
        actor=make_platform_actor(AppScope.TENANT),
        service=FakeProvisioningService(),
    )

    response = client.post(
        "/api/platform/tenants",
        headers={
            "X-Request-Id": "req_wrong_scope",
            "X-CSRF-Token": "csrf",
            "Idempotency-Key": "tenant-create-1",
        },
        json={
            "name": "Cafe Demo",
            "subdomain": "demo-cafe",
            "gsmNumber": "+905551112233",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "wrong_app_scope"


def test_create_tenant_requires_csrf_token() -> None:
    client = make_client(
        actor=make_platform_actor(),
        service=FakeProvisioningService(),
    )

    response = client.post(
        "/api/platform/tenants",
        headers={"X-Request-Id": "req_csrf", "Idempotency-Key": "tenant-create-1"},
        json={
            "name": "Cafe Demo",
            "subdomain": "demo-cafe",
            "gsmNumber": "+905551112233",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_required"


def test_create_tenant_requires_idempotency_key() -> None:
    client = make_client(
        actor=make_platform_actor(),
        service=FakeProvisioningService(),
    )

    response = client.post(
        "/api/platform/tenants",
        headers={"X-Request-Id": "req_idempotency", "X-CSRF-Token": "csrf"},
        json={
            "name": "Cafe Demo",
            "subdomain": "demo-cafe",
            "gsmNumber": "+905551112233",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_create_tenant_passes_normalized_command_to_provisioning_service() -> None:
    service = FakeProvisioningService()
    client = make_client(actor=make_platform_actor(), service=service)

    response = client.post(
        "/api/platform/tenants",
        headers={
            "X-Request-Id": "req_create_tenant",
            "X-CSRF-Token": "csrf",
            "Idempotency-Key": "tenant-create-1",
        },
        json={
            "name": "Cafe Demo",
            "subdomain": "Demo-Cafe",
            "gsmNumber": "+905551112233",
            "sector": "CAFE",
            "capacity": 24,
            "address": {"city": "Istanbul"},
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "tenantId": str(TENANT_ID),
        "status": "active",
        "subdomain": "demo-cafe",
        "starterTemplateApplied": True,
        "failureSummary": None,
        "dnsReady": False,
    }
    assert service.actor == make_platform_actor()
    assert service.command == CreateTenantCommand(
        name="Cafe Demo",
        subdomain="demo-cafe",
        gsm_number="+905551112233",
        sector="cafe",
        capacity=24,
        address='{"city":"Istanbul"}',
    )
    assert service.idempotency_key == "tenant-create-1"


def test_get_tenant_provisioning_state_returns_safe_state() -> None:
    service = FakeProvisioningService()
    client = make_client(actor=make_platform_actor(), service=service)

    response = client.get(f"/api/platform/tenants/{TENANT_ID}/provisioning")

    assert response.status_code == 200
    assert response.json() == {
        "tenantId": str(TENANT_ID),
        "tenantStatus": "provisioning_failed",
        "starterApplicationStatus": "failed",
        "templateKey": "cafe_default",
        "templateVersion": 1,
        "failureSummary": "starter template failed",
        "dnsReady": False,
        "createdAt": "2026-07-02T12:00:00+00:00",
        "updatedAt": "2026-07-02T12:00:00+00:00",
    }
    assert service.state_tenant_id == TENANT_ID


def test_get_tenant_provisioning_recovery_summary_returns_safe_summary() -> None:
    service = FakeProvisioningService()
    client = make_client(actor=make_platform_actor(), service=service)

    response = client.get(f"/api/platform/tenants/{TENANT_ID}/provisioning/recovery-summary")

    assert response.status_code == 200
    assert response.json() == {
        "tenantId": str(TENANT_ID),
        "missingRequiredRecords": ["halls", "stations"],
        "completedPhases": ["tenant_admin_user"],
        "failedPhase": "starter_template",
        "safeRetryAllowed": True,
        "failureSummary": "starter template failed",
    }
    assert service.summary_tenant_id == TENANT_ID


def test_retry_tenant_provisioning_requires_csrf_and_calls_service() -> None:
    service = FakeProvisioningService()
    client = make_client(actor=make_platform_actor(), service=service)

    response = client.post(
        f"/api/platform/tenants/{TENANT_ID}/provisioning/retry",
        headers={"X-CSRF-Token": "csrf"},
        json={"recoveryNote": "reviewed safe failure"},
    )

    assert response.status_code == 200
    assert response.json()["tenantStatus"] == "active"
    assert service.retry_args == {
        "actor": make_platform_actor(),
        "tenant_id": TENANT_ID,
        "recovery_note": "reviewed safe failure",
    }


def test_mark_tenant_provisioning_recovery_needed_requires_reason() -> None:
    service = FakeProvisioningService()
    client = make_client(actor=make_platform_actor(), service=service)

    response = client.post(
        f"/api/platform/tenants/{TENANT_ID}/provisioning/recovery-needed",
        headers={"X-CSRF-Token": "csrf"},
        json={"reason": "manual data inspection required"},
    )

    assert response.status_code == 200
    assert response.json()["starterApplicationStatus"] == "recovery_needed"
    assert service.recovery_needed_args == {
        "actor": make_platform_actor(),
        "tenant_id": TENANT_ID,
        "reason": "manual data inspection required",
    }


def test_list_tenants_returns_platform_safe_health_response() -> None:
    query_service = FakeTenantRegistryQueryService()
    client = make_client(actor=make_platform_actor(), query_service=query_service)

    response = client.get(
        "/api/platform/tenants?status=active&sector=CAFE&q= demo &cursor=0&limit=200",
        headers={"X-Request-Id": "req_list_tenants"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "tenantId": str(TENANT_ID),
                "name": "Cafe Demo",
                "subdomain": "demo-cafe",
                "status": "active",
                "dnsReady": False,
                "sector": "cafe",
                "provisioningState": "ready",
                "lastLifecycleEventAt": "2026-07-02T12:00:00+00:00",
                "healthFlags": ["dns_not_ready"],
                "createdAt": "2026-07-02T12:00:00+00:00",
                "updatedAt": "2026-07-02T12:00:00+00:00",
            }
        ],
        "page": {"nextCursor": "50", "limit": 100},
    }
    assert query_service.list_args == {
        "status": "active",
        "sector": "cafe",
        "q": "demo",
        "cursor": 0,
        "limit": 100,
    }


def test_get_tenant_returns_platform_profile_response() -> None:
    query_service = FakeTenantRegistryQueryService()
    client = make_client(actor=make_platform_actor(), query_service=query_service)

    response = client.get(
        f"/api/platform/tenants/{TENANT_ID}",
        headers={"X-Request-Id": "req_get_tenant"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "tenantId": str(TENANT_ID),
        "name": "Cafe Demo",
        "subdomain": "demo-cafe",
        "gsmNumber": "+905551112233",
        "sector": "cafe",
        "capacity": 24,
        "address": '{"city":"Istanbul"}',
        "status": "active",
        "dnsReady": False,
        "provisioningState": "ready",
        "starterTemplateState": "applied",
        "tenantAdminBootstrapState": "first_password_required",
        "healthFlags": ["dns_not_ready"],
        "createdAt": "2026-07-02T12:00:00+00:00",
        "updatedAt": "2026-07-02T12:00:00+00:00",
    }
    assert query_service.detail_tenant_id == TENANT_ID


def test_list_tenant_lifecycle_events_returns_platform_timeline() -> None:
    query_service = FakeTenantRegistryQueryService()
    client = make_client(actor=make_platform_actor(), query_service=query_service)

    response = client.get(
        f"/api/platform/tenants/{TENANT_ID}/lifecycle-events?cursor=25&limit=200",
        headers={"X-Request-Id": "req_get_tenant_lifecycle"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "eventId": "44444444-4444-4444-4444-444444444444",
                "tenantId": str(TENANT_ID),
                "previousStatus": "active",
                "nextStatus": "suspended",
                "actorUserId": str(PLATFORM_USER_ID),
                "reason": "manual maintenance",
                "createdAt": "2026-07-02T12:05:00+00:00",
            }
        ],
        "page": {"nextCursor": "50", "limit": 100},
    }
    assert query_service.lifecycle_args == {
        "tenant_id": TENANT_ID,
        "cursor": 25,
        "limit": 100,
    }


def test_update_tenant_profile_passes_editable_fields_to_mutation_service() -> None:
    mutation_service = FakeTenantRegistryMutationService()
    client = make_client(actor=make_platform_actor(), mutation_service=mutation_service)

    response = client.patch(
        f"/api/platform/tenants/{TENANT_ID}/profile",
        headers={"X-CSRF-Token": "csrf"},
        json={
            "gsmNumber": "+905559998877",
            "sector": "CAFE",
            "capacity": 32,
            "address": {"city": "Ankara"},
        },
    )

    assert response.status_code == 200
    assert response.json()["gsmNumber"] == "+905559998877"
    assert mutation_service.profile_args == {
        "actor": make_platform_actor(),
        "tenant_id": TENANT_ID,
        "command": TenantProfileUpdateCommand(
            fields={
                "gsm_number": "+905559998877",
                "sector": "cafe",
                "capacity": 32,
                "address": '{"city":"Ankara"}',
            },
        ),
    }


def test_update_tenant_profile_only_passes_provided_patch_fields() -> None:
    mutation_service = FakeTenantRegistryMutationService()
    client = make_client(actor=make_platform_actor(), mutation_service=mutation_service)

    response = client.patch(
        f"/api/platform/tenants/{TENANT_ID}/profile",
        headers={"X-CSRF-Token": "csrf"},
        json={"gsmNumber": "+905559998877"},
    )

    assert response.status_code == 200
    assert mutation_service.profile_args == {
        "actor": make_platform_actor(),
        "tenant_id": TENANT_ID,
        "command": TenantProfileUpdateCommand(fields={"gsm_number": "+905559998877"}),
    }


def test_update_tenant_profile_requires_csrf() -> None:
    client = make_client(
        actor=make_platform_actor(),
        mutation_service=FakeTenantRegistryMutationService(),
    )

    response = client.patch(
        f"/api/platform/tenants/{TENANT_ID}/profile",
        json={"gsmNumber": "+905559998877"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_required"


def test_set_dns_ready_calls_mutation_service() -> None:
    mutation_service = FakeTenantRegistryMutationService()
    client = make_client(actor=make_platform_actor(), mutation_service=mutation_service)

    response = client.post(
        f"/api/platform/tenants/{TENANT_ID}/dns-ready",
        headers={"X-CSRF-Token": "csrf"},
        json={"dnsReady": True},
    )

    assert response.status_code == 200
    assert response.json()["dnsReady"] is True
    assert mutation_service.dns_args == {
        "actor": make_platform_actor(),
        "tenant_id": TENANT_ID,
        "dns_ready": True,
    }


def test_change_tenant_status_requires_reason_and_calls_mutation_service() -> None:
    mutation_service = FakeTenantRegistryMutationService()
    client = make_client(actor=make_platform_actor(), mutation_service=mutation_service)

    response = client.post(
        f"/api/platform/tenants/{TENANT_ID}/status",
        headers={"X-CSRF-Token": "csrf"},
        json={"nextStatus": "suspended", "reason": "manual maintenance"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "suspended"
    assert mutation_service.status_args == {
        "actor": make_platform_actor(),
        "tenant_id": TENANT_ID,
        "next_status": "suspended",
        "reason": "manual maintenance",
    }
