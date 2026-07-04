from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import order_items, preparation_items, preparation_transitions
from iotables.security.context import ActorContext, StaffRole


@dataclass(frozen=True)
class PreparationQueueItem:
    preparation_item_id: UUID
    order_item_id: UUID
    station_id: UUID
    item_label: str
    variant_label: str
    quantity: int
    note: str | None
    status: str
    ordered_at: datetime
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "preparationItemId": str(self.preparation_item_id),
            "orderItemId": str(self.order_item_id),
            "stationId": str(self.station_id),
            "itemLabel": self.item_label,
            "variantLabel": self.variant_label,
            "quantity": self.quantity,
            "note": self.note,
            "status": self.status,
            "orderedAt": self.ordered_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class PreparationQueue:
    items: tuple[PreparationQueueItem, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {"items": [item.as_api_payload() for item in self.items]}


class PreparationQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_station_queue(
        self,
        *,
        actor: ActorContext,
        station_id: UUID,
        status: str | None = None,
    ) -> PreparationQueue:
        require_station_staff(actor)
        if actor.tenant_id is None:
            raise not_authorized()
        ensure_station_scope(actor, station_id)
        filters = [
            preparation_items.c.tenant_id == actor.tenant_id,
            preparation_items.c.station_id == station_id,
        ]
        if status:
            filters.append(preparation_items.c.status == status)
        else:
            filters.append(preparation_items.c.status.in_(("pending", "preparing", "ready")))
        return PreparationQueue(items=await list_queue_items(self.session, filters=filters))


class PreparationMutationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start_preparing(
        self,
        *,
        actor: ActorContext,
        preparation_item_id: UUID,
    ) -> PreparationQueueItem:
        return await self._transition(
            actor=actor,
            preparation_item_id=preparation_item_id,
            allowed_from={"pending"},
            to_status="preparing",
            reason=None,
        )

    async def mark_ready(
        self,
        *,
        actor: ActorContext,
        preparation_item_id: UUID,
    ) -> PreparationQueueItem:
        return await self._transition(
            actor=actor,
            preparation_item_id=preparation_item_id,
            allowed_from={"preparing"},
            to_status="ready",
            reason=None,
        )

    async def report_cannot_prepare(
        self,
        *,
        actor: ActorContext,
        preparation_item_id: UUID,
        reason: str,
    ) -> PreparationQueueItem:
        if not reason.strip():
            raise reason_required()
        return await self._transition(
            actor=actor,
            preparation_item_id=preparation_item_id,
            allowed_from={"pending", "preparing"},
            to_status="cannot_prepare",
            reason=reason.strip(),
        )

    async def _transition(
        self,
        *,
        actor: ActorContext,
        preparation_item_id: UUID,
        allowed_from: set[str],
        to_status: str,
        reason: str | None,
    ) -> PreparationQueueItem:
        require_station_staff(actor)
        if actor.tenant_id is None or actor.user_id is None:
            raise not_authorized()
        row = await self._load_preparation_item(
            tenant_id=actor.tenant_id,
            preparation_item_id=preparation_item_id,
        )
        if row is None:
            raise not_found()
        ensure_station_scope(actor, row["station_id"])
        if row["status"] not in allowed_from:
            raise invalid_preparation_transition()

        now = datetime.now(UTC)
        result = await self.session.execute(
            update(preparation_items)
            .where(
                preparation_items.c.tenant_id == actor.tenant_id,
                preparation_items.c.id == preparation_item_id,
                preparation_items.c.status == row["status"],
            )
            .values(
                status=to_status,
                cannot_prepare_reason=reason,
                updated_by_user_id=actor.user_id,
                updated_at=now,
            )
            .returning(preparation_items.c.id)
        )
        if result.mappings().first() is None:
            raise invalid_preparation_transition()
        await self.session.execute(
            insert(preparation_transitions).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                preparation_item_id=preparation_item_id,
                actor_user_id=actor.user_id,
                from_status=row["status"],
                to_status=to_status,
                reason=reason,
                created_at=now,
            )
        )
        await self.session.commit()
        items = await list_queue_items(
            self.session,
            filters=[
                preparation_items.c.tenant_id == actor.tenant_id,
                preparation_items.c.id == preparation_item_id,
            ],
        )
        if not items:
            raise not_found()
        return items[0]

    async def _load_preparation_item(self, *, tenant_id: UUID, preparation_item_id: UUID):
        return (
            (
                await self.session.execute(
                    select(preparation_items).where(
                        preparation_items.c.tenant_id == tenant_id,
                        preparation_items.c.id == preparation_item_id,
                    )
                )
            )
            .mappings()
            .first()
        )


async def list_queue_items(
    session: AsyncSession,
    *,
    filters: list[object],
) -> tuple[PreparationQueueItem, ...]:
    rows = (
        (
            await session.execute(
                select(
                    preparation_items.c.id.label("preparation_item_id"),
                    preparation_items.c.order_item_id,
                    preparation_items.c.station_id,
                    preparation_items.c.status,
                    preparation_items.c.updated_at,
                    preparation_items.c.created_at,
                    order_items.c.name_snapshot,
                    order_items.c.variant_name_snapshot,
                    order_items.c.quantity,
                    order_items.c.note,
                )
                .select_from(
                    preparation_items.join(
                        order_items,
                        (order_items.c.tenant_id == preparation_items.c.tenant_id)
                        & (order_items.c.id == preparation_items.c.order_item_id),
                    )
                )
                .where(*filters)
                .order_by(preparation_items.c.created_at)
            )
        )
        .mappings()
        .all()
    )
    return tuple(
        PreparationQueueItem(
            preparation_item_id=row["preparation_item_id"],
            order_item_id=row["order_item_id"],
            station_id=row["station_id"],
            item_label=row["name_snapshot"],
            variant_label=row["variant_name_snapshot"],
            quantity=row["quantity"],
            note=row["note"],
            status=row["status"],
            ordered_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    )


def require_station_staff(actor: ActorContext) -> None:
    if StaffRole.STATION_STAFF not in actor.roles:
        raise not_authorized()


def ensure_station_scope(actor: ActorContext, station_id: UUID) -> None:
    actor_station_ids = getattr(actor, "station_ids", frozenset())
    if actor_station_ids and station_id not in actor_station_ids:
        raise outside_station_scope()


def not_authorized() -> ApiError:
    return ApiError(status_code=403, code="not_authorized", message="Not authorized.")


def outside_station_scope() -> ApiError:
    return ApiError(
        status_code=403,
        code="outside_station_scope",
        message="Station is outside actor scope.",
    )


def not_found() -> ApiError:
    return ApiError(status_code=404, code="not_found_or_hidden", message="Not found.")


def reason_required() -> ApiError:
    return ApiError(status_code=422, code="reason_required", message="Reason is required.")


def invalid_preparation_transition() -> ApiError:
    return ApiError(
        status_code=409,
        code="invalid_preparation_transition",
        message="Preparation item status does not allow this transition.",
    )
