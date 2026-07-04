from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.service_staff import (
    get_service_delivery_mutation_service,
    get_service_delivery_query_service,
)
from iotables.main import create_app
from iotables.modules.fulfillment.service_delivery import (
    BulkDeliveryResult,
    DeliveryStateResult,
    ServiceReadyItem,
    ServiceReadyItemList,
)
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole

TENANT_ID = UUID("33333333-3333-3333-3333-333333333333")
USER_ID = UUID("44444444-4444-4444-4444-444444444444")
HALL_ID = UUID("55555555-5555-5555-5555-555555555555")
TABLE_ID = UUID("66666666-6666-6666-6666-666666666666")
PREPARATION_ITEM_ID = UUID("88888888-8888-8888-8888-888888888888")
ORDER_ITEM_ID = UUID("99999999-9999-9999-9999-999999999999")


class FakeSessionResolver:
    def __init__(self, actor: ActorContext | None) -> None:
        self.actor = actor

    async def resolve(self, session_token: str) -> ActorContext | None:
        return self.actor if session_token == "service-token" else None


class FakeServiceDeliveryQueryService:
    def __init__(self) -> None:
        self.args: dict[str, object] | None = None

    async def list_ready_items(
        self,
        *,
        actor: ActorContext,
        hall_id: UUID | None = None,
        status: str | None = None,
    ) -> ServiceReadyItemList:
        self.args = {"actor": actor, "hall_id": hall_id, "status": status}
        return ServiceReadyItemList(items=(make_ready_item(),))


class FakeServiceDeliveryMutationService:
    def __init__(self) -> None:
        self.pickup_args: dict[str, object] | None = None
        self.deliver_args: dict[str, object] | None = None
        self.bulk_args: dict[str, object] | None = None

    async def mark_picked_up(
        self,
        *,
        actor: ActorContext,
        order_item_id: UUID,
    ) -> DeliveryStateResult:
        self.pickup_args = {"actor": actor, "order_item_id": order_item_id}
        return make_delivery_state(status="picked_up")

    async def mark_delivered(
        self,
        *,
        actor: ActorContext,
        order_item_id: UUID,
    ) -> DeliveryStateResult:
        self.deliver_args = {"actor": actor, "order_item_id": order_item_id}
        return make_delivery_state(status="delivered")

    async def bulk_mark_delivered(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
        order_item_ids: tuple[UUID, ...],
        idempotency_key: str,
        request_hash: str,
    ) -> BulkDeliveryResult:
        self.bulk_args = {
            "actor": actor,
            "table_id": table_id,
            "order_item_ids": order_item_ids,
            "idempotency_key": idempotency_key,
            "request_hash": request_hash,
        }
        return BulkDeliveryResult(
            table_id=table_id,
            delivered_items=(make_delivery_state(status="delivered"),),
            already_delivered_items=(),
            delivered_at=datetime(2026, 7, 3, 12, 10, tzinfo=UTC),
            actor_display_name=None,
            duplicate=False,
        )


def make_ready_item() -> ServiceReadyItem:
    return ServiceReadyItem(
        order_item_id=ORDER_ITEM_ID,
        preparation_item_id=PREPARATION_ITEM_ID,
        table_id=TABLE_ID,
        hall_id=HALL_ID,
        table_label="Masa 001",
        item_label="Americano",
        quantity=1,
        preparation_ready_at=datetime(2026, 7, 3, 12, 5, tzinfo=UTC),
        delivery_status=None,
    )


def make_delivery_state(*, status: str) -> DeliveryStateResult:
    delivered_at = datetime(2026, 7, 3, 12, 10, tzinfo=UTC) if status == "delivered" else None
    picked_up_at = datetime(2026, 7, 3, 12, 8, tzinfo=UTC) if status == "picked_up" else None
    return DeliveryStateResult(
        order_item_id=ORDER_ITEM_ID,
        preparation_item_id=PREPARATION_ITEM_ID,
        status=status,
        picked_up_at=picked_up_at,
        delivered_at=delivered_at,
        actor_display_name=None,
    )


def make_actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.TENANT_USER,
        app_scope=AppScope.SERVICE,
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        roles=frozenset({StaffRole.SERVICE_STAFF}),
    )


def test_service_staff_ready_items_uses_actor_scope_and_hall_filter() -> None:
    service = FakeServiceDeliveryQueryService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_service_delivery_query_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "service-token")

    response = client.get(f"/api/v1/service-staff/ready-items?hallId={HALL_ID}")

    assert response.status_code == 200
    assert response.json()["items"][0]["itemLabel"] == "Americano"
    assert service.args is not None
    assert service.args["hall_id"] == HALL_ID


def test_service_staff_delivery_transitions_require_csrf_and_bind_actor() -> None:
    service = FakeServiceDeliveryMutationService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_service_delivery_mutation_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "service-token")

    missing_csrf = client.post(f"/api/v1/service-staff/items/{ORDER_ITEM_ID}/pick-up")
    pickup = client.post(
        f"/api/v1/service-staff/items/{ORDER_ITEM_ID}/pick-up",
        headers={"X-CSRF-Token": "csrf"},
    )
    deliver = client.post(
        f"/api/v1/service-staff/items/{ORDER_ITEM_ID}/deliver",
        headers={"X-CSRF-Token": "csrf"},
    )

    assert missing_csrf.status_code == 403
    assert pickup.status_code == 200
    assert pickup.json()["status"] == "picked_up"
    assert deliver.status_code == 200
    assert deliver.json()["status"] == "delivered"
    assert service.pickup_args is not None
    assert service.pickup_args["order_item_id"] == ORDER_ITEM_ID
    assert service.deliver_args is not None
    assert service.deliver_args["order_item_id"] == ORDER_ITEM_ID


def test_service_staff_bulk_delivery_requires_idempotency_and_uses_request_hash() -> None:
    service = FakeServiceDeliveryMutationService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_service_delivery_mutation_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "service-token")
    payload = {"tableId": str(TABLE_ID), "orderItemIds": [str(ORDER_ITEM_ID)]}

    missing_key = client.post(
        "/api/v1/service-staff/items/bulk-deliver",
        headers={"X-CSRF-Token": "csrf"},
        json=payload,
    )
    delivered = client.post(
        "/api/v1/service-staff/items/bulk-deliver",
        headers={"X-CSRF-Token": "csrf", "Idempotency-Key": "bulk-1"},
        json=payload,
    )

    assert missing_key.status_code == 400
    assert missing_key.json()["error"]["code"] == "idempotency_key_required"
    assert delivered.status_code == 200
    assert delivered.json()["deliveredItems"][0]["status"] == "delivered"
    assert service.bulk_args is not None
    assert service.bulk_args["table_id"] == TABLE_ID
    assert service.bulk_args["order_item_ids"] == (ORDER_ITEM_ID,)
    assert service.bulk_args["idempotency_key"] == "bulk-1"
    assert isinstance(service.bulk_args["request_hash"], str)
    assert len(service.bulk_args["request_hash"]) == 64
