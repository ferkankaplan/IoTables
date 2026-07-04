from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import audit_events, preparation_items, product_services, stations
from iotables.security.context import ActorContext


@dataclass(frozen=True)
class Station:
    station_id: UUID
    name: str
    display_order: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "stationId": str(self.station_id),
            "name": self.name,
            "displayOrder": self.display_order,
            "enabled": self.enabled,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class StationList:
    items: tuple[Station, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {"items": [station.as_api_payload() for station in self.items]}


@dataclass(frozen=True)
class StationWriteCommand:
    name: str
    display_order: int


class StationSetupQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_stations(
        self,
        *,
        tenant_id: UUID,
        include_disabled: bool = False,
    ) -> StationList:
        filters = [stations.c.tenant_id == tenant_id]
        if not include_disabled:
            filters.append(stations.c.enabled.is_(True))
        rows = (
            (
                await self.session.execute(
                    select(stations)
                    .where(*filters)
                    .order_by(stations.c.display_order, stations.c.name)
                )
            )
            .mappings()
            .all()
        )
        return StationList(items=tuple(station_from_row(row) for row in rows))


class StationSetupMutationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_station(
        self,
        *,
        actor: ActorContext,
        command: StationWriteCommand,
    ) -> Station:
        tenant_id = require_tenant_id(actor)
        station_id = uuid4()
        now = utc_now()
        try:
            await self.session.execute(
                insert(stations).values(
                    id=station_id,
                    tenant_id=tenant_id,
                    name=command.name,
                    display_order=command.display_order,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self._audit(
                tenant_id=tenant_id,
                actor=actor,
                action="station.changed",
                target_id=station_id,
                metadata={"operation": "station.created", "name": command.name},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_station() from exc

        return Station(
            station_id=station_id,
            name=command.name,
            display_order=command.display_order,
            enabled=True,
            created_at=now,
            updated_at=now,
        )

    async def update_station(
        self,
        *,
        actor: ActorContext,
        station_id: UUID,
        command: StationWriteCommand,
    ) -> Station:
        tenant_id = require_tenant_id(actor)
        if await self._load_station(tenant_id=tenant_id, station_id=station_id) is None:
            raise not_found()

        now = utc_now()
        try:
            await self.session.execute(
                update(stations)
                .where(stations.c.tenant_id == tenant_id, stations.c.id == station_id)
                .values(
                    name=command.name,
                    display_order=command.display_order,
                    updated_at=now,
                )
            )
            await self._audit(
                tenant_id=tenant_id,
                actor=actor,
                action="station.changed",
                target_id=station_id,
                metadata={"operation": "station.updated"},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_station() from exc

        row = await self._load_station(tenant_id=tenant_id, station_id=station_id)
        if row is None:
            raise not_found()
        return station_from_row(row)

    async def disable_station(
        self,
        *,
        actor: ActorContext,
        station_id: UUID,
        reason: str,
    ) -> Station:
        tenant_id = require_tenant_id(actor)
        if not reason.strip():
            raise reason_required()
        row = await self._load_station(tenant_id=tenant_id, station_id=station_id)
        if row is None:
            raise not_found()
        if await self._station_has_orderable_products(tenant_id=tenant_id, station_id=station_id):
            raise station_has_orderable_products()
        if await self._station_has_active_queue(tenant_id=tenant_id, station_id=station_id):
            raise station_has_active_queue()

        now = utc_now()
        await self.session.execute(
            update(stations)
            .where(stations.c.tenant_id == tenant_id, stations.c.id == station_id)
            .values(enabled=False, updated_at=now)
        )
        await self._audit(
            tenant_id=tenant_id,
            actor=actor,
            action="station.disabled",
            target_id=station_id,
            reason=reason.strip(),
            metadata={"operation": "station.disabled"},
            now=now,
        )
        await self.session.commit()
        updated = await self._load_station(tenant_id=tenant_id, station_id=station_id)
        if updated is None:
            raise not_found()
        return station_from_row(updated)

    async def _load_station(self, *, tenant_id: UUID, station_id: UUID):
        return (
            (
                await self.session.execute(
                    select(stations).where(
                        stations.c.tenant_id == tenant_id,
                        stations.c.id == station_id,
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _station_has_orderable_products(self, *, tenant_id: UUID, station_id: UUID) -> bool:
        product_count = await self.session.scalar(
            select(func.count())
            .select_from(product_services)
            .where(
                product_services.c.tenant_id == tenant_id,
                product_services.c.station_id == station_id,
                product_services.c.enabled.is_(True),
            )
        )
        return bool(product_count)

    async def _station_has_active_queue(self, *, tenant_id: UUID, station_id: UUID) -> bool:
        active_count = await self.session.scalar(
            select(func.count())
            .select_from(preparation_items)
            .where(
                preparation_items.c.tenant_id == tenant_id,
                preparation_items.c.station_id == station_id,
                preparation_items.c.status.in_(("pending", "preparing")),
            )
        )
        return bool(active_count)

    async def _audit(
        self,
        *,
        tenant_id: UUID,
        actor: ActorContext,
        action: str,
        target_id: UUID,
        metadata: dict[str, object],
        now: datetime,
        reason: str | None = None,
    ) -> None:
        await self.session.execute(
            insert(audit_events).values(
                id=uuid4(),
                tenant_id=tenant_id,
                actor_user_id=actor.user_id,
                action=action,
                target_type="station",
                target_id=str(target_id),
                reason=reason,
                metadata=metadata,
                created_at=now,
            )
        )


def station_from_row(row) -> Station:
    return Station(
        station_id=row["id"],
        name=row["name"],
        display_order=row["display_order"],
        enabled=row["enabled"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def require_tenant_id(actor: ActorContext) -> UUID:
    if actor.tenant_id is None:
        raise ApiError(
            status_code=403,
            code="wrong_scope",
            message="This session is not bound to a tenant.",
        )
    return actor.tenant_id


def utc_now() -> datetime:
    return datetime.now(UTC)


def duplicate_station() -> ApiError:
    return ApiError(status_code=409, code="duplicate_station", message="Station already exists.")


def station_has_orderable_products() -> ApiError:
    return ApiError(
        status_code=409,
        code="station_has_orderable_products",
        message="Enabled menu items still route to this station.",
    )


def station_has_active_queue() -> ApiError:
    return ApiError(
        status_code=409,
        code="station_has_active_queue",
        message="Active preparation work blocks this action.",
    )


def reason_required() -> ApiError:
    return ApiError(status_code=422, code="reason_required", message="Reason is required.")


def not_found() -> ApiError:
    return ApiError(
        status_code=404,
        code="not_found_or_hidden",
        message="Resource was not found.",
    )
