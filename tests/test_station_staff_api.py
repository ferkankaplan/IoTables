from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.station_staff import (
    get_preparation_mutation_service,
    get_preparation_query_service,
)
from iotables.main import create_app
from iotables.modules.fulfillment.preparation import PreparationQueue, PreparationQueueItem
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole

TENANT_ID = UUID("33333333-3333-3333-3333-333333333333")
USER_ID = UUID("44444444-4444-4444-4444-444444444444")
STATION_ID = UUID("77777777-7777-7777-7777-777777777777")
PREPARATION_ITEM_ID = UUID("88888888-8888-8888-8888-888888888888")
ORDER_ITEM_ID = UUID("99999999-9999-9999-9999-999999999999")


class FakeSessionResolver:
    def __init__(self, actor: ActorContext | None) -> None:
        self.actor = actor

    async def resolve(self, session_token: str) -> ActorContext | None:
        return self.actor if session_token == "station-token" else None


class FakePreparationQueryService:
    def __init__(self) -> None:
        self.args: dict[str, object] | None = None

    async def list_station_queue(
        self,
        *,
        actor: ActorContext,
        station_id: UUID,
        status: str | None = None,
    ) -> PreparationQueue:
        self.args = {"actor": actor, "station_id": station_id, "status": status}
        return PreparationQueue(
            items=(
                PreparationQueueItem(
                    preparation_item_id=PREPARATION_ITEM_ID,
                    order_item_id=ORDER_ITEM_ID,
                    station_id=station_id,
                    item_label="Americano",
                    variant_label="Standart",
                    quantity=1,
                    note=None,
                    status="pending",
                    ordered_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
                    updated_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
                ),
            )
        )


class FakePreparationMutationService:
    def __init__(self) -> None:
        self.start_args: dict[str, object] | None = None
        self.ready_args: dict[str, object] | None = None
        self.cannot_args: dict[str, object] | None = None

    async def start_preparing(
        self,
        *,
        actor: ActorContext,
        preparation_item_id: UUID,
    ) -> PreparationQueueItem:
        self.start_args = {"actor": actor, "preparation_item_id": preparation_item_id}
        return make_queue_item(status="preparing")

    async def mark_ready(
        self,
        *,
        actor: ActorContext,
        preparation_item_id: UUID,
    ) -> PreparationQueueItem:
        self.ready_args = {"actor": actor, "preparation_item_id": preparation_item_id}
        return make_queue_item(status="ready")

    async def report_cannot_prepare(
        self,
        *,
        actor: ActorContext,
        preparation_item_id: UUID,
        reason: str,
    ) -> PreparationQueueItem:
        self.cannot_args = {
            "actor": actor,
            "preparation_item_id": preparation_item_id,
            "reason": reason,
        }
        return make_queue_item(status="cannot_prepare")


def make_queue_item(*, status: str = "pending") -> PreparationQueueItem:
    return PreparationQueueItem(
        preparation_item_id=PREPARATION_ITEM_ID,
        order_item_id=ORDER_ITEM_ID,
        station_id=STATION_ID,
        item_label="Americano",
        variant_label="Standart",
        quantity=1,
        note=None,
        status=status,
        ordered_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
    )


def make_actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.TENANT_USER,
        app_scope=AppScope.STATION,
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        roles=frozenset({StaffRole.STATION_STAFF}),
    )


def test_station_staff_queue_uses_actor_scope_and_station_filter() -> None:
    service = FakePreparationQueryService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_preparation_query_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "station-token")

    response = client.get(f"/api/station-staff/queue?station_id={STATION_ID}&status=pending")

    assert response.status_code == 200
    assert response.json()["items"][0]["itemLabel"] == "Americano"
    assert service.args is not None
    assert service.args["station_id"] == STATION_ID
    assert service.args["status"] == "pending"


def test_station_staff_preparation_transitions_require_csrf_and_bind_actor() -> None:
    service = FakePreparationMutationService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_preparation_mutation_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "station-token")

    missing_csrf = client.post(
        f"/api/station-staff/preparation-items/{PREPARATION_ITEM_ID}/start"
    )
    start = client.post(
        f"/api/station-staff/preparation-items/{PREPARATION_ITEM_ID}/start",
        headers={"X-CSRF-Token": "csrf"},
    )
    ready = client.post(
        f"/api/station-staff/preparation-items/{PREPARATION_ITEM_ID}/mark-ready",
        headers={"X-CSRF-Token": "csrf"},
    )
    cannot = client.post(
        f"/api/station-staff/preparation-items/{PREPARATION_ITEM_ID}/cannot-prepare",
        headers={"X-CSRF-Token": "csrf"},
        json={"reason": "stok yok"},
    )

    assert missing_csrf.status_code == 403
    assert start.status_code == 200
    assert start.json()["status"] == "preparing"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert cannot.status_code == 200
    assert cannot.json()["status"] == "cannot_prepare"
    assert service.start_args is not None
    assert service.start_args["preparation_item_id"] == PREPARATION_ITEM_ID
    assert service.cannot_args is not None
    assert service.cannot_args["reason"] == "stok yok"
