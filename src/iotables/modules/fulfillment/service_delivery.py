from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import (
    delivery_bulk_idempotency,
    delivery_states,
    delivery_transitions,
    order_items,
    orders,
    preparation_items,
    staff_hall_assignments,
    table_sessions,
    tenant_operational_settings,
    venue_tables,
)
from iotables.security.context import ActorContext, StaffRole


@dataclass(frozen=True)
class ServiceReadyItem:
    order_item_id: UUID
    preparation_item_id: UUID
    table_id: UUID
    hall_id: UUID
    table_label: str
    item_label: str
    quantity: int
    preparation_ready_at: datetime
    delivery_status: str | None

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "orderItemId": str(self.order_item_id),
            "preparationItemId": str(self.preparation_item_id),
            "tableId": str(self.table_id),
            "hallId": str(self.hall_id),
            "tableLabel": self.table_label,
            "itemLabel": self.item_label,
            "quantity": self.quantity,
            "preparationReadyAt": self.preparation_ready_at.isoformat(),
            "deliveryStatus": self.delivery_status,
        }


@dataclass(frozen=True)
class ServiceReadyItemList:
    items: tuple[ServiceReadyItem, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {"items": [item.as_api_payload() for item in self.items]}


@dataclass(frozen=True)
class DeliveryStateResult:
    order_item_id: UUID
    preparation_item_id: UUID
    status: str
    picked_up_at: datetime | None
    delivered_at: datetime | None
    actor_display_name: str | None

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "orderItemId": str(self.order_item_id),
            "preparationItemId": str(self.preparation_item_id),
            "status": self.status,
            "pickedUpAt": self.picked_up_at.isoformat() if self.picked_up_at else None,
            "deliveredAt": self.delivered_at.isoformat() if self.delivered_at else None,
            "actorDisplayName": self.actor_display_name,
        }


@dataclass(frozen=True)
class BulkDeliveryResult:
    table_id: UUID
    delivered_items: tuple[DeliveryStateResult, ...]
    already_delivered_items: tuple[UUID, ...]
    delivered_at: datetime
    actor_display_name: str | None
    duplicate: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tableId": str(self.table_id),
            "deliveredItems": [item.as_api_payload() for item in self.delivered_items],
            "alreadyDeliveredItems": [str(item_id) for item_id in self.already_delivered_items],
            "deliveredAt": self.delivered_at.isoformat(),
            "actorDisplayName": self.actor_display_name,
            "duplicate": self.duplicate,
        }


class ServiceDeliveryQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_ready_items(
        self,
        *,
        actor: ActorContext,
        hall_id: UUID | None = None,
        status: str | None = None,
    ) -> ServiceReadyItemList:
        await require_service_staff_context(self.session, actor)
        if hall_id is not None:
            await ensure_hall_scope(self.session, actor, hall_id)
        rows = await self.session.execute(
            service_item_select()
            .where(*ready_item_filters(actor=actor, hall_id=hall_id, status=status))
            .order_by(preparation_items.c.updated_at, order_items.c.created_at)
        )
        return ServiceReadyItemList(items=tuple(to_ready_item(row) for row in rows.mappings()))


class ServiceDeliveryMutationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def mark_picked_up(
        self,
        *,
        actor: ActorContext,
        order_item_id: UUID,
    ) -> DeliveryStateResult:
        return await self._transition(
            actor=actor,
            order_item_id=order_item_id,
            to_status="picked_up",
        )

    async def mark_delivered(
        self,
        *,
        actor: ActorContext,
        order_item_id: UUID,
    ) -> DeliveryStateResult:
        return await self._transition(
            actor=actor,
            order_item_id=order_item_id,
            to_status="delivered",
        )

    async def bulk_mark_delivered(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
        order_item_ids: tuple[UUID, ...],
        idempotency_key: str,
        request_hash: str,
    ) -> BulkDeliveryResult:
        await require_service_staff_context(self.session, actor)
        if actor.tenant_id is None or actor.user_id is None:
            raise not_authorized()
        if not idempotency_key.strip():
            raise idempotency_key_required()
        normalized_ids = tuple(dict.fromkeys(order_item_ids))
        if not normalized_ids or len(normalized_ids) != len(order_item_ids):
            raise bulk_item_invalid()

        existing_idempotency = await self._load_bulk_idempotency(
            actor=actor,
            idempotency_key=idempotency_key,
        )
        if existing_idempotency is not None:
            if existing_idempotency["request_hash"] != request_hash:
                raise idempotency_conflict()
            if existing_idempotency["status"] == "completed":
                return await self._bulk_replay_result(
                    actor=actor,
                    table_id=table_id,
                    order_item_ids=tuple(
                        UUID(value) for value in existing_idempotency["delivered_order_item_ids"]
                    ),
                    delivered_at=existing_idempotency["completed_at"],
                )
            raise idempotency_conflict()

        now = datetime.now(UTC)
        await self.session.execute(
            insert(delivery_bulk_idempotency).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                actor_user_id=actor.user_id,
                table_id=table_id,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                delivered_order_item_ids=None,
                status="processing",
                created_at=now,
                completed_at=None,
            )
        )

        item_rows = await self._load_bulk_ready_items(actor=actor, order_item_ids=normalized_ids)
        if len(item_rows) != len(normalized_ids):
            raise bulk_item_invalid()
        table_ids = {row["table_id"] for row in item_rows}
        if table_ids != {table_id}:
            raise bulk_mixed_table()
        await ensure_hall_scope(self.session, actor, item_rows[0]["hall_id"])

        delivered_items = []
        for row in item_rows:
            existing_state = await self._load_delivery_state(
                actor=actor,
                order_item_id=row["order_item_id"],
            )
            if existing_state is not None and existing_state["status"] == "delivered":
                raise bulk_item_invalid()
            delivered_items.append(
                await self._apply_delivery_transition(
                    actor=actor,
                    item=row,
                    existing=existing_state,
                    to_status="delivered",
                    now=now,
                )
            )

        await self.session.execute(
            update(delivery_bulk_idempotency)
            .where(
                delivery_bulk_idempotency.c.tenant_id == actor.tenant_id,
                delivery_bulk_idempotency.c.actor_user_id == actor.user_id,
                delivery_bulk_idempotency.c.idempotency_key == idempotency_key,
            )
            .values(
                delivered_order_item_ids=[str(item.order_item_id) for item in delivered_items],
                status="completed",
                completed_at=now,
            )
        )
        await self.session.commit()
        return BulkDeliveryResult(
            table_id=table_id,
            delivered_items=tuple(delivered_items),
            already_delivered_items=(),
            delivered_at=now,
            actor_display_name=None,
            duplicate=False,
        )

    async def _transition(
        self,
        *,
        actor: ActorContext,
        order_item_id: UUID,
        to_status: str,
    ) -> DeliveryStateResult:
        await require_service_staff_context(self.session, actor)
        if actor.tenant_id is None or actor.user_id is None:
            raise not_authorized()
        item = await self._load_ready_item(actor=actor, order_item_id=order_item_id)
        if item is None:
            raise not_ready_for_delivery()
        await ensure_hall_scope(self.session, actor, item["hall_id"])

        existing = await self._load_delivery_state(actor=actor, order_item_id=order_item_id)
        if existing is not None and existing["status"] == "delivered":
            if to_status == "delivered":
                return to_delivery_state_result(item=item, state=existing)
            raise invalid_delivery_transition()
        if existing is not None and existing["status"] == to_status:
            return to_delivery_state_result(item=item, state=existing)

        now = datetime.now(UTC)
        from_status = existing["status"] if existing is not None else None
        if to_status == "picked_up" and from_status is not None:
            raise invalid_delivery_transition()
        if to_status == "delivered" and from_status not in (None, "picked_up"):
            raise invalid_delivery_transition()

        await self._apply_delivery_transition(
            actor=actor,
            item=item,
            existing=existing,
            to_status=to_status,
            now=now,
        )
        await self.session.commit()
        state = await self._load_delivery_state(actor=actor, order_item_id=order_item_id)
        if state is None:
            raise not_found()
        return to_delivery_state_result(item=item, state=state)

    async def _load_ready_item(self, *, actor: ActorContext, order_item_id: UUID):
        row = await self.session.execute(
            service_item_select().where(
                preparation_items.c.tenant_id == actor.tenant_id,
                order_items.c.id == order_item_id,
                preparation_items.c.status == "ready",
                order_items.c.voided_at.is_(None),
            )
        )
        return row.mappings().first()

    async def _load_bulk_idempotency(self, *, actor: ActorContext, idempotency_key: str):
        row = await self.session.execute(
            select(delivery_bulk_idempotency).where(
                delivery_bulk_idempotency.c.tenant_id == actor.tenant_id,
                delivery_bulk_idempotency.c.actor_user_id == actor.user_id,
                delivery_bulk_idempotency.c.idempotency_key == idempotency_key,
            )
        )
        return row.mappings().first()

    async def _load_bulk_ready_items(
        self,
        *,
        actor: ActorContext,
        order_item_ids: tuple[UUID, ...],
    ) -> tuple[Any, ...]:
        rows = await self.session.execute(
            service_item_select()
            .where(
                preparation_items.c.tenant_id == actor.tenant_id,
                order_items.c.id.in_(order_item_ids),
                preparation_items.c.status == "ready",
                order_items.c.voided_at.is_(None),
            )
            .order_by(order_items.c.id)
        )
        return tuple(rows.mappings())

    async def _apply_delivery_transition(
        self,
        *,
        actor: ActorContext,
        item: Any,
        existing: Any,
        to_status: str,
        now: datetime,
    ) -> DeliveryStateResult:
        if actor.tenant_id is None or actor.user_id is None:
            raise not_authorized()
        from_status = existing["status"] if existing is not None else None
        if to_status == "picked_up" and from_status is not None:
            raise invalid_delivery_transition()
        if to_status == "delivered" and from_status not in (None, "picked_up"):
            raise invalid_delivery_transition()

        if existing is None:
            delivery_state_id = uuid4()
            await self.session.execute(
                insert(delivery_states).values(
                    id=delivery_state_id,
                    tenant_id=actor.tenant_id,
                    order_item_id=item["order_item_id"],
                    status=to_status,
                    updated_by_user_id=actor.user_id,
                    updated_at=now,
                    created_at=now,
                )
            )
        else:
            delivery_state_id = existing["delivery_state_id"]
            result = await self.session.execute(
                update(delivery_states)
                .where(
                    delivery_states.c.tenant_id == actor.tenant_id,
                    delivery_states.c.order_item_id == item["order_item_id"],
                    delivery_states.c.status == from_status,
                )
                .values(
                    status=to_status,
                    updated_by_user_id=actor.user_id,
                    updated_at=now,
                )
                .returning(delivery_states.c.id)
            )
            if result.mappings().first() is None:
                raise invalid_delivery_transition()

        await self.session.execute(
            insert(delivery_transitions).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                delivery_state_id=delivery_state_id,
                order_item_id=item["order_item_id"],
                actor_user_id=actor.user_id,
                from_status=from_status,
                to_status=to_status,
                created_at=now,
            )
        )
        return DeliveryStateResult(
            order_item_id=item["order_item_id"],
            preparation_item_id=item["preparation_item_id"],
            status=to_status,
            picked_up_at=now if to_status == "picked_up" else None,
            delivered_at=now if to_status == "delivered" else None,
            actor_display_name=None,
        )

    async def _bulk_replay_result(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
        order_item_ids: tuple[UUID, ...],
        delivered_at: datetime,
    ) -> BulkDeliveryResult:
        item_rows = await self._load_bulk_ready_items(actor=actor, order_item_ids=order_item_ids)
        delivered_items = []
        for row in item_rows:
            state = await self._load_delivery_state(actor=actor, order_item_id=row["order_item_id"])
            if state is not None:
                delivered_items.append(to_delivery_state_result(item=row, state=state))
        return BulkDeliveryResult(
            table_id=table_id,
            delivered_items=tuple(delivered_items),
            already_delivered_items=tuple(item.order_item_id for item in delivered_items),
            delivered_at=delivered_at,
            actor_display_name=None,
            duplicate=True,
        )

    async def _load_delivery_state(self, *, actor: ActorContext, order_item_id: UUID):
        row = await self.session.execute(
            select(
                delivery_states.c.id.label("delivery_state_id"),
                delivery_states.c.order_item_id,
                delivery_states.c.status,
                delivery_states.c.created_at,
                delivery_states.c.updated_at,
            ).where(
                delivery_states.c.tenant_id == actor.tenant_id,
                delivery_states.c.order_item_id == order_item_id,
            )
        )
        return row.mappings().first()


def service_item_select():
    return select(
        order_items.c.id.label("order_item_id"),
        preparation_items.c.id.label("preparation_item_id"),
        table_sessions.c.table_id,
        venue_tables.c.hall_id,
        venue_tables.c.name.label("table_label"),
        order_items.c.name_snapshot.label("item_label"),
        order_items.c.quantity,
        preparation_items.c.updated_at.label("preparation_ready_at"),
        delivery_states.c.status.label("delivery_status"),
    ).select_from(
        preparation_items.join(
            order_items,
            (order_items.c.tenant_id == preparation_items.c.tenant_id)
            & (order_items.c.id == preparation_items.c.order_item_id),
        )
        .join(
            orders,
            (orders.c.tenant_id == order_items.c.tenant_id)
            & (orders.c.id == order_items.c.order_id),
        )
        .join(
            table_sessions,
            (table_sessions.c.tenant_id == orders.c.tenant_id)
            & (table_sessions.c.id == orders.c.table_session_id),
        )
        .join(
            venue_tables,
            (venue_tables.c.tenant_id == table_sessions.c.tenant_id)
            & (venue_tables.c.id == table_sessions.c.table_id),
        )
        .outerjoin(
            delivery_states,
            (delivery_states.c.tenant_id == order_items.c.tenant_id)
            & (delivery_states.c.order_item_id == order_items.c.id),
        )
    )


def ready_item_filters(
    *,
    actor: ActorContext,
    hall_id: UUID | None,
    status: str | None,
) -> list[object]:
    filters = [
        preparation_items.c.tenant_id == actor.tenant_id,
        preparation_items.c.status == "ready",
        order_items.c.voided_at.is_(None),
    ]
    if hall_id is not None:
        filters.append(venue_tables.c.hall_id == hall_id)
    if status is not None:
        filters.append(delivery_states.c.status == status)
    else:
        filters.append(
            or_(delivery_states.c.status.is_(None), delivery_states.c.status == "picked_up")
        )
    return filters


def to_ready_item(row: Any) -> ServiceReadyItem:
    return ServiceReadyItem(
        order_item_id=row["order_item_id"],
        preparation_item_id=row["preparation_item_id"],
        table_id=row["table_id"],
        hall_id=row["hall_id"],
        table_label=row["table_label"],
        item_label=row["item_label"],
        quantity=row["quantity"],
        preparation_ready_at=row["preparation_ready_at"],
        delivery_status=row["delivery_status"],
    )


def to_delivery_state_result(*, item: Any, state: Any) -> DeliveryStateResult:
    status = state["status"]
    return DeliveryStateResult(
        order_item_id=item["order_item_id"],
        preparation_item_id=item["preparation_item_id"],
        status=status,
        picked_up_at=state["created_at"] if status == "picked_up" else None,
        delivered_at=state["updated_at"] if status == "delivered" else None,
        actor_display_name=None,
    )


async def require_service_staff_context(session: AsyncSession, actor: ActorContext) -> None:
    if (
        actor.tenant_id is None
        or actor.user_id is None
        or StaffRole.SERVICE_STAFF not in actor.roles
    ):
        raise not_authorized()
    settings_row = await session.execute(
        select(tenant_operational_settings.c.service_delivery_tracking_enabled).where(
            tenant_operational_settings.c.tenant_id == actor.tenant_id
        )
    )
    if settings_row.scalar_one_or_none() is not True:
        raise service_tracking_disabled()


async def ensure_hall_scope(session: AsyncSession, actor: ActorContext, hall_id: UUID) -> None:
    if actor.tenant_id is None or actor.user_id is None:
        raise not_authorized()
    row = await session.execute(
        select(staff_hall_assignments.c.id).where(
            and_(
                staff_hall_assignments.c.tenant_id == actor.tenant_id,
                staff_hall_assignments.c.user_id == actor.user_id,
                staff_hall_assignments.c.hall_id == hall_id,
                staff_hall_assignments.c.status == "active",
            )
        )
    )
    if row.scalar_one_or_none() is None:
        raise outside_hall_scope()


def not_authorized() -> ApiError:
    return ApiError(status_code=403, code="not_authorized", message="Not authorized.")


def service_tracking_disabled() -> ApiError:
    return ApiError(
        status_code=403,
        code="service_tracking_disabled",
        message="Service delivery tracking is disabled.",
    )


def outside_hall_scope() -> ApiError:
    return ApiError(
        status_code=403,
        code="outside_hall_scope",
        message="Hall is outside actor scope.",
    )


def not_ready_for_delivery() -> ApiError:
    return ApiError(
        status_code=409,
        code="not_ready_for_delivery",
        message="Item is not ready for delivery.",
    )


def invalid_delivery_transition() -> ApiError:
    return ApiError(
        status_code=409,
        code="invalid_delivery_transition",
        message="Delivery state does not allow this transition.",
    )


def bulk_mixed_table() -> ApiError:
    return ApiError(
        status_code=409,
        code="bulk_mixed_table",
        message="Bulk delivery items must belong to the requested table.",
    )


def bulk_item_invalid() -> ApiError:
    return ApiError(
        status_code=409,
        code="bulk_item_invalid",
        message="At least one bulk delivery item is invalid.",
    )


def idempotency_conflict() -> ApiError:
    return ApiError(
        status_code=409,
        code="idempotency_conflict",
        message="Idempotency key was already used for a different request.",
    )


def idempotency_key_required() -> ApiError:
    return ApiError(
        status_code=400,
        code="idempotency_key_required",
        message="Idempotency-Key header is required.",
    )


def not_found() -> ApiError:
    return ApiError(status_code=404, code="not_found_or_hidden", message="Not found.")
