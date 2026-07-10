from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import audit_events, halls, table_sessions, venue_tables
from iotables.security.context import ActorContext

TABLES_PER_HALL = 100
TABLE_MODE_VIRTUAL_TEST = "virtual_test"
TABLE_MODE_PHYSICAL = "physical"


@dataclass(frozen=True)
class VenueTable:
    table_id: UUID
    hall_id: UUID
    table_number: int
    name: str
    display_order: int
    mode: str
    enabled: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tableId": str(self.table_id),
            "hallId": str(self.hall_id),
            "tableNumber": self.table_number,
            "name": self.name,
            "displayOrder": self.display_order,
            "mode": self.mode,
            "systemBoundarySlot": is_system_boundary_slot(self.table_number),
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class HallWithTables:
    hall_id: UUID
    name: str
    display_order: int
    table_number_base: int
    enabled: bool
    tables: tuple[VenueTable, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "hallId": str(self.hall_id),
            "name": self.name,
            "displayOrder": self.display_order,
            "tableNumberBase": self.table_number_base,
            "enabled": self.enabled,
            "tables": [table.as_api_payload() for table in self.tables],
        }


@dataclass(frozen=True)
class HallTableBoard:
    halls: tuple[HallWithTables, ...]
    derived_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "halls": [hall.as_api_payload() for hall in self.halls],
            "derivedAt": self.derived_at.isoformat(),
        }


class VenueLayoutQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_hall_table_board(self, *, tenant_id: UUID) -> HallTableBoard:
        hall_rows = (
            (
                await self.session.execute(
                    select(halls)
                    .where(halls.c.tenant_id == tenant_id)
                    .order_by(halls.c.display_order, halls.c.name)
                )
            )
            .mappings()
            .all()
        )
        table_rows = (
            (
                await self.session.execute(
                    select(venue_tables)
                    .where(venue_tables.c.tenant_id == tenant_id)
                    .order_by(
                        venue_tables.c.hall_id,
                        venue_tables.c.display_order,
                        venue_tables.c.name,
                    )
                )
            )
            .mappings()
            .all()
        )

        tables_by_hall: dict[UUID, list[VenueTable]] = {}
        for row in table_rows:
            tables_by_hall.setdefault(row["hall_id"], []).append(table_from_row(row))

        return HallTableBoard(
            halls=tuple(
                HallWithTables(
                    hall_id=row["id"],
                    name=row["name"],
                    display_order=row["display_order"],
                    table_number_base=row["table_number_base"],
                    enabled=row["enabled"],
                    tables=tuple(tables_by_hall.get(row["id"], ())),
                )
                for row in hall_rows
            ),
            derived_at=datetime.now(UTC),
        )


@dataclass(frozen=True)
class HallWriteCommand:
    name: str
    display_order: int


@dataclass(frozen=True)
class TableWriteCommand:
    name: str
    display_order: int
    hall_id: UUID | None = None
    enabled: bool | None = None
    mode: str | None = None


class VenueLayoutMutationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_hall(
        self,
        *,
        actor: ActorContext,
        command: HallWriteCommand,
    ) -> HallWithTables:
        tenant_id = require_tenant_id(actor)
        hall_id = uuid4()
        now = utc_now()
        table_number_base = table_number_base_for_display_order(command.display_order)
        table_rows = [
            {
                "id": uuid4(),
                "tenant_id": tenant_id,
                "hall_id": hall_id,
                "table_number": table_number_base + offset,
                "name": f"Masa {table_number_base + offset}",
                "display_order": offset + 1,
                "mode": TABLE_MODE_VIRTUAL_TEST,
                "enabled": True,
                "created_at": now,
                "updated_at": now,
            }
            for offset in range(TABLES_PER_HALL)
        ]
        try:
            await self.session.execute(
                insert(halls).values(
                    id=hall_id,
                    tenant_id=tenant_id,
                    name=command.name,
                    display_order=command.display_order,
                    table_number_base=table_number_base,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self.session.execute(insert(venue_tables).values(table_rows))
            await self._audit(
                tenant_id=tenant_id,
                actor=actor,
                action="venue_layout.changed",
                target_type="hall",
                target_id=hall_id,
                metadata={
                    "operation": "hall.created",
                    "name": command.name,
                    "tableNumberBase": table_number_base,
                    "tableSlotCount": TABLES_PER_HALL,
                },
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_hall() from exc

        return HallWithTables(
            hall_id=hall_id,
            name=command.name,
            display_order=command.display_order,
            table_number_base=table_number_base,
            enabled=True,
            tables=tuple(table_from_row(row) for row in table_rows),
        )

    async def update_hall(
        self,
        *,
        actor: ActorContext,
        hall_id: UUID,
        command: HallWriteCommand,
    ) -> HallWithTables:
        tenant_id = require_tenant_id(actor)
        existing = await self._load_hall(tenant_id=tenant_id, hall_id=hall_id)
        if existing is None:
            raise not_found()

        now = utc_now()
        try:
            await self.session.execute(
                update(halls)
                .where(halls.c.tenant_id == tenant_id, halls.c.id == hall_id)
                .values(
                    name=command.name,
                    display_order=command.display_order,
                    updated_at=now,
                )
            )
            await self._audit(
                tenant_id=tenant_id,
                actor=actor,
                action="venue_layout.changed",
                target_type="hall",
                target_id=hall_id,
                metadata={"operation": "hall.updated"},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_hall() from exc

        board = await VenueLayoutQueryService(self.session).get_hall_table_board(
            tenant_id=tenant_id
        )
        return next(hall for hall in board.halls if hall.hall_id == hall_id)

    async def disable_hall(
        self,
        *,
        actor: ActorContext,
        hall_id: UUID,
        reason: str,
    ) -> HallWithTables:
        tenant_id = require_tenant_id(actor)
        if not reason.strip():
            raise reason_required()
        existing = await self._load_hall(tenant_id=tenant_id, hall_id=hall_id)
        if existing is None:
            raise not_found()
        if await self._active_sessions_in_hall(tenant_id=tenant_id, hall_id=hall_id):
            raise active_session_blocks_disable()

        now = utc_now()
        await self.session.execute(
            update(halls)
            .where(halls.c.tenant_id == tenant_id, halls.c.id == hall_id)
            .values(enabled=False, updated_at=now)
        )
        await self._audit(
            tenant_id=tenant_id,
            actor=actor,
            action="venue_layout.changed",
            target_type="hall",
            target_id=hall_id,
            reason=reason.strip(),
            metadata={"operation": "hall.disabled"},
            now=now,
        )
        await self.session.commit()
        board = await VenueLayoutQueryService(self.session).get_hall_table_board(
            tenant_id=tenant_id
        )
        return next(hall for hall in board.halls if hall.hall_id == hall_id)

    async def create_table(
        self,
        *,
        actor: ActorContext,
        hall_id: UUID,
        command: TableWriteCommand,
    ) -> VenueTable:
        tenant_id = require_tenant_id(actor)
        hall_row = await self._load_hall(tenant_id=tenant_id, hall_id=hall_id)
        if hall_row is None:
            raise not_found()
        table_number = hall_row["table_number_base"] + command.display_order - 1
        if not table_number_in_hall_range(
            table_number=table_number,
            table_number_base=hall_row["table_number_base"],
        ):
            raise validation_failed("Table order is outside the hall's 100-slot range.")

        table_id = uuid4()
        now = utc_now()
        mode = command.mode or TABLE_MODE_VIRTUAL_TEST
        validate_table_mode(table_number=table_number, mode=mode)
        try:
            await self.session.execute(
                insert(venue_tables).values(
                    id=table_id,
                    tenant_id=tenant_id,
                    hall_id=hall_id,
                    table_number=table_number,
                    name=command.name,
                    display_order=command.display_order,
                    mode=mode,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self._audit(
                tenant_id=tenant_id,
                actor=actor,
                action="venue_layout.changed",
                target_type="table",
                target_id=table_id,
                metadata={"operation": "table.created", "hallId": str(hall_id)},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_table() from exc

        return VenueTable(
            table_id=table_id,
            hall_id=hall_id,
            table_number=table_number,
            name=command.name,
            display_order=command.display_order,
            mode=mode,
            enabled=True,
        )

    async def update_table(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
        command: TableWriteCommand,
    ) -> VenueTable:
        tenant_id = require_tenant_id(actor)
        existing = await self._load_table(tenant_id=tenant_id, table_id=table_id)
        if existing is None:
            raise not_found()
        next_hall_id = command.hall_id or existing["hall_id"]
        next_hall = await self._load_hall(tenant_id=tenant_id, hall_id=next_hall_id)
        if next_hall is None:
            raise not_found()
        if not table_number_in_hall_range(
            table_number=existing["table_number"],
            table_number_base=next_hall["table_number_base"],
        ):
            raise validation_failed("Table number is outside the target hall's range.")
        next_mode = command.mode or existing["mode"]
        validate_table_mode(table_number=existing["table_number"], mode=next_mode)

        now = utc_now()
        try:
            await self.session.execute(
                update(venue_tables)
                .where(venue_tables.c.tenant_id == tenant_id, venue_tables.c.id == table_id)
                .values(
                    hall_id=next_hall_id,
                    name=command.name,
                    display_order=command.display_order,
                    mode=next_mode,
                    enabled=existing["enabled"] if command.enabled is None else command.enabled,
                    updated_at=now,
                )
            )
            await self._audit(
                tenant_id=tenant_id,
                actor=actor,
                action="venue_layout.changed",
                target_type="table",
                target_id=table_id,
                metadata={"operation": "table.updated", "hallId": str(next_hall_id)},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_table() from exc

        updated = await self._load_table(tenant_id=tenant_id, table_id=table_id)
        if updated is None:
            raise not_found()
        return table_from_row(updated)

    async def disable_table(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
        reason: str,
    ) -> VenueTable:
        tenant_id = require_tenant_id(actor)
        if not reason.strip():
            raise reason_required()
        existing = await self._load_table(tenant_id=tenant_id, table_id=table_id)
        if existing is None:
            raise not_found()
        if await self._active_session_for_table(tenant_id=tenant_id, table_id=table_id):
            raise active_session_blocks_disable()

        now = utc_now()
        await self.session.execute(
            update(venue_tables)
            .where(venue_tables.c.tenant_id == tenant_id, venue_tables.c.id == table_id)
            .values(enabled=False, updated_at=now)
        )
        await self._audit(
            tenant_id=tenant_id,
            actor=actor,
            action="table.disabled",
            target_type="table",
            target_id=table_id,
            reason=reason.strip(),
            metadata={"operation": "table.disabled", "hallId": str(existing["hall_id"])},
            now=now,
        )
        await self.session.commit()
        updated = await self._load_table(tenant_id=tenant_id, table_id=table_id)
        if updated is None:
            raise not_found()
        return table_from_row(updated)

    async def _load_hall(self, *, tenant_id: UUID, hall_id: UUID):
        return (
            (
                await self.session.execute(
                    select(halls).where(halls.c.tenant_id == tenant_id, halls.c.id == hall_id)
                )
            )
            .mappings()
            .first()
        )

    async def _load_table(self, *, tenant_id: UUID, table_id: UUID):
        return (
            (
                await self.session.execute(
                    select(venue_tables).where(
                        venue_tables.c.tenant_id == tenant_id,
                        venue_tables.c.id == table_id,
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _active_session_for_table(self, *, tenant_id: UUID, table_id: UUID) -> bool:
        active_id = await self.session.scalar(
            select(table_sessions.c.id).where(
                table_sessions.c.tenant_id == tenant_id,
                table_sessions.c.table_id == table_id,
                table_sessions.c.status == "open",
            )
        )
        return active_id is not None

    async def _active_sessions_in_hall(self, *, tenant_id: UUID, hall_id: UUID) -> bool:
        active_count = await self.session.scalar(
            select(func.count())
            .select_from(table_sessions)
            .join(
                venue_tables,
                (venue_tables.c.tenant_id == table_sessions.c.tenant_id)
                & (venue_tables.c.id == table_sessions.c.table_id),
            )
            .where(
                table_sessions.c.tenant_id == tenant_id,
                venue_tables.c.hall_id == hall_id,
                table_sessions.c.status == "open",
            )
        )
        return bool(active_count)

    async def _audit(
        self,
        *,
        tenant_id: UUID,
        actor: ActorContext,
        action: str,
        target_type: str,
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
                target_type=target_type,
                target_id=str(target_id),
                reason=reason,
                metadata=metadata,
                created_at=now,
            )
        )


def table_from_row(row) -> VenueTable:
    return VenueTable(
        table_id=row["id"],
        hall_id=row["hall_id"],
        table_number=row["table_number"],
        name=row["name"],
        display_order=row["display_order"],
        mode=row["mode"],
        enabled=row["enabled"],
    )


def table_number_base_for_display_order(display_order: int) -> int:
    return display_order * TABLES_PER_HALL


def table_number_in_hall_range(*, table_number: int, table_number_base: int) -> bool:
    return table_number_base <= table_number < table_number_base + TABLES_PER_HALL


def is_system_boundary_slot(table_number: int) -> bool:
    return table_number % TABLES_PER_HALL in (0, TABLES_PER_HALL - 1)


def validate_table_mode(*, table_number: int, mode: str) -> None:
    if mode not in {TABLE_MODE_VIRTUAL_TEST, TABLE_MODE_PHYSICAL}:
        raise validation_failed("Unsupported table mode.")
    if mode == TABLE_MODE_PHYSICAL and is_system_boundary_slot(table_number):
        raise validation_failed("Boundary table slots cannot become physical.")


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


def duplicate_hall() -> ApiError:
    return ApiError(status_code=409, code="duplicate_hall", message="Hall already exists.")


def duplicate_table() -> ApiError:
    return ApiError(status_code=409, code="duplicate_table", message="Table already exists.")


def not_found() -> ApiError:
    return ApiError(
        status_code=404,
        code="not_found_or_hidden",
        message="Resource was not found.",
    )


def reason_required() -> ApiError:
    return ApiError(status_code=422, code="reason_required", message="Reason is required.")


def active_session_blocks_disable() -> ApiError:
    return ApiError(
        status_code=409,
        code="active_session_blocks_disable",
        message="An active table session blocks this action.",
    )


def validation_failed(message: str) -> ApiError:
    return ApiError(status_code=422, code="validation_failed", message=message)
