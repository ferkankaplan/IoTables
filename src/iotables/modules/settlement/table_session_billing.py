from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import desc, distinct, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import (
    audit_events,
    checks,
    halls,
    order_items,
    orders,
    payments,
    session_closures,
    table_sessions,
    venue_tables,
)
from iotables.security.context import ActorContext, StaffRole


@dataclass(frozen=True)
class CashierTableState:
    table_id: UUID
    hall_id: UUID
    table_label: str
    hall_label: str
    mode: str
    table_session_id: UUID | None
    check_id: UUID | None
    status: str
    opened_at: datetime | None
    total_minor: int
    paid_minor: int
    remaining_minor: int

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tableId": str(self.table_id),
            "hallId": str(self.hall_id),
            "tableLabel": self.table_label,
            "hallLabel": self.hall_label,
            "mode": self.mode,
            "tableSessionId": str(self.table_session_id) if self.table_session_id else None,
            "checkId": str(self.check_id) if self.check_id else None,
            "status": self.status,
            "openedAt": self.opened_at.isoformat() if self.opened_at else None,
            "totalMinor": self.total_minor,
            "paidMinor": self.paid_minor,
            "remainingMinor": self.remaining_minor,
        }


@dataclass(frozen=True)
class CashierVenueBoard:
    tables: tuple[CashierTableState, ...]
    derived_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tables": [table.as_api_payload() for table in self.tables],
            "derivedAt": self.derived_at.isoformat(),
        }


@dataclass(frozen=True)
class ActiveTableSession:
    table_session_id: UUID
    table_id: UUID
    hall_id: UUID
    check_id: UUID
    status: str
    opened_at: datetime
    table_label: str
    hall_label: str

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tableSessionId": str(self.table_session_id),
            "tableId": str(self.table_id),
            "hallId": str(self.hall_id),
            "checkId": str(self.check_id),
            "status": self.status,
            "openedAt": self.opened_at.isoformat(),
            "tableLabel": self.table_label,
            "hallLabel": self.hall_label,
        }


@dataclass(frozen=True)
class BillSummary:
    check_id: UUID
    table_session_id: UUID
    total_minor: int
    paid_minor: int
    remaining_minor: int
    currency: str
    order_count: int
    payment_count: int

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "checkId": str(self.check_id),
            "tableSessionId": str(self.table_session_id),
            "totalMinor": self.total_minor,
            "paidMinor": self.paid_minor,
            "remainingMinor": self.remaining_minor,
            "currency": self.currency,
            "orderCount": self.order_count,
            "paymentCount": self.payment_count,
        }


@dataclass(frozen=True)
class ClosedTableSession:
    table_session_id: UUID
    check_id: UUID
    closed_at: datetime
    status: str

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tableSessionId": str(self.table_session_id),
            "checkId": str(self.check_id),
            "closedAt": self.closed_at.isoformat(),
            "status": self.status,
        }


class TableSessionBillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def venue_board(
        self, *, actor: ActorContext, include_virtual_test_tables: bool = False
    ) -> CashierVenueBoard:
        require_cashier(actor)
        if actor.tenant_id is None:
            raise not_authorized()
        filters = [
            venue_tables.c.tenant_id == actor.tenant_id,
            venue_tables.c.enabled.is_(True),
            halls.c.enabled.is_(True),
        ]
        if not include_virtual_test_tables:
            filters.append(venue_tables.c.mode == "physical")

        table_rows = (
            (
                await self.session.execute(
                    select(
                        venue_tables.c.id.label("table_id"),
                        venue_tables.c.name.label("table_label"),
                        venue_tables.c.mode.label("mode"),
                        halls.c.id.label("hall_id"),
                        halls.c.name.label("hall_label"),
                    )
                    .select_from(
                        venue_tables.join(
                            halls,
                            (halls.c.tenant_id == venue_tables.c.tenant_id)
                            & (halls.c.id == venue_tables.c.hall_id),
                        )
                    )
                    .where(*filters)
                    .order_by(halls.c.display_order, venue_tables.c.display_order)
                )
            )
            .mappings()
            .all()
        )
        states = []
        for row in table_rows:
            active = await self._active_session_row(
                tenant_id=actor.tenant_id,
                table_id=row["table_id"],
            )
            if active is None:
                states.append(
                    CashierTableState(
                        table_id=row["table_id"],
                        hall_id=row["hall_id"],
                        table_label=row["table_label"],
                        hall_label=row["hall_label"],
                        mode=row["mode"],
                        table_session_id=None,
                        check_id=None,
                        status="empty",
                        opened_at=None,
                        total_minor=0,
                        paid_minor=0,
                        remaining_minor=0,
                    )
                )
                continue
            summary = await self.get_bill_summary(
                actor=actor,
                table_session_id=active["table_session_id"],
            )
            states.append(
                CashierTableState(
                    table_id=row["table_id"],
                    hall_id=row["hall_id"],
                    table_label=row["table_label"],
                    hall_label=row["hall_label"],
                    mode=row["mode"],
                    table_session_id=active["table_session_id"],
                    check_id=active["check_id"],
                    status="occupied",
                    opened_at=active["opened_at"],
                    total_minor=summary.total_minor,
                    paid_minor=summary.paid_minor,
                    remaining_minor=summary.remaining_minor,
                )
            )
        return CashierVenueBoard(tables=tuple(states), derived_at=datetime.now(UTC))

    async def get_active_table_session(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
    ) -> ActiveTableSession:
        require_cashier(actor)
        if actor.tenant_id is None:
            raise not_authorized()
        row = await self._active_session_row(tenant_id=actor.tenant_id, table_id=table_id)
        if row is None:
            raise not_found()
        return ActiveTableSession(
            table_session_id=row["table_session_id"],
            table_id=row["table_id"],
            hall_id=row["hall_id"],
            check_id=row["check_id"],
            status=row["status"],
            opened_at=row["opened_at"],
            table_label=row["table_label"],
            hall_label=row["hall_label"],
        )

    async def get_bill_summary(
        self,
        *,
        actor: ActorContext,
        table_session_id: UUID,
    ) -> BillSummary:
        require_cashier(actor)
        if actor.tenant_id is None:
            raise not_authorized()
        check_row = await self._check_for_session(
            tenant_id=actor.tenant_id,
            table_session_id=table_session_id,
        )
        if check_row is None:
            raise not_found()
        return await self.bill_summary_for_check(
            tenant_id=actor.tenant_id,
            check_id=check_row["check_id"],
            table_session_id=table_session_id,
        )

    async def bill_summary_for_check(
        self,
        *,
        tenant_id: UUID,
        check_id: UUID,
        table_session_id: UUID,
    ) -> BillSummary:
        total_minor = await self._total_minor(
            tenant_id=tenant_id,
            table_session_id=table_session_id,
        )
        paid_minor = await self.paid_minor(tenant_id=tenant_id, check_id=check_id)
        currency = await self._currency(tenant_id=tenant_id, table_session_id=table_session_id)
        order_count = await self._order_count(
            tenant_id=tenant_id,
            table_session_id=table_session_id,
        )
        payment_count = await self._payment_count(tenant_id=tenant_id, check_id=check_id)
        return BillSummary(
            check_id=check_id,
            table_session_id=table_session_id,
            total_minor=total_minor,
            paid_minor=paid_minor,
            remaining_minor=max(total_minor - paid_minor, 0),
            currency=currency,
            order_count=order_count,
            payment_count=payment_count,
        )

    async def close_session(
        self,
        *,
        actor: ActorContext,
        table_session_id: UUID,
        reason: str | None,
    ) -> ClosedTableSession:
        require_cashier(actor)
        if actor.tenant_id is None or actor.user_id is None:
            raise not_authorized()
        session_row = await self._check_for_session(
            tenant_id=actor.tenant_id,
            table_session_id=table_session_id,
        )
        if session_row is None:
            raise not_found()
        if session_row["check_status"] == "closed" and session_row["session_status"] == "closed":
            closure = await self._closure_row(
                tenant_id=actor.tenant_id,
                table_session_id=table_session_id,
            )
            if closure is None:
                raise invalid_state()
            return ClosedTableSession(
                table_session_id=table_session_id,
                check_id=session_row["check_id"],
                closed_at=closure["closed_at"],
                status="closed",
            )
        if session_row["check_status"] != "open" or session_row["session_status"] != "open":
            raise check_closed()
        summary = await self.bill_summary_for_check(
            tenant_id=actor.tenant_id,
            check_id=session_row["check_id"],
            table_session_id=table_session_id,
        )
        if summary.remaining_minor != 0:
            raise remaining_balance_not_zero()
        now = datetime.now(UTC)
        await self.session.execute(
            update(checks)
            .where(
                checks.c.tenant_id == actor.tenant_id,
                checks.c.id == session_row["check_id"],
            )
            .values(status="closed", closed_at=now)
        )
        await self.session.execute(
            update(table_sessions)
            .where(
                table_sessions.c.tenant_id == actor.tenant_id,
                table_sessions.c.id == table_session_id,
            )
            .values(status="closed", closed_at=now, updated_at=now)
        )
        await self.session.execute(
            insert(session_closures).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                table_session_id=table_session_id,
                check_id=session_row["check_id"],
                cashier_user_id=actor.user_id,
                reason=reason.strip() if reason else None,
                closed_at=now,
            )
        )
        await self.session.execute(
            insert(audit_events).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                actor_user_id=actor.user_id,
                action="session.closed",
                target_type="table_session",
                target_id=str(table_session_id),
                reason=reason.strip() if reason else None,
                metadata={"checkId": str(session_row["check_id"])},
                created_at=now,
            )
        )
        await self.session.commit()
        return ClosedTableSession(
            table_session_id=table_session_id,
            check_id=session_row["check_id"],
            closed_at=now,
            status="closed",
        )

    async def paid_minor(self, *, tenant_id: UUID, check_id: UUID) -> int:
        return int(
            (
                await self.session.execute(
                    select(func.coalesce(func.sum(payments.c.amount_minor), 0)).where(
                        payments.c.tenant_id == tenant_id,
                        payments.c.check_id == check_id,
                        payments.c.status == "recorded",
                    )
                )
            ).scalar_one()
            or 0
        )

    async def _active_session_row(self, *, tenant_id: UUID, table_id: UUID):
        row = await self.session.execute(
            select(
                table_sessions.c.id.label("table_session_id"),
                table_sessions.c.table_id,
                table_sessions.c.status,
                table_sessions.c.opened_at,
                checks.c.id.label("check_id"),
                venue_tables.c.hall_id,
                venue_tables.c.name.label("table_label"),
                halls.c.name.label("hall_label"),
            )
            .select_from(
                table_sessions.join(
                    checks,
                    (checks.c.tenant_id == table_sessions.c.tenant_id)
                    & (checks.c.table_session_id == table_sessions.c.id),
                )
                .join(
                    venue_tables,
                    (venue_tables.c.tenant_id == table_sessions.c.tenant_id)
                    & (venue_tables.c.id == table_sessions.c.table_id),
                )
                .join(
                    halls,
                    (halls.c.tenant_id == venue_tables.c.tenant_id)
                    & (halls.c.id == venue_tables.c.hall_id),
                )
            )
            .where(
                table_sessions.c.tenant_id == tenant_id,
                table_sessions.c.table_id == table_id,
                table_sessions.c.status == "open",
            )
        )
        return row.mappings().first()

    async def _check_for_session(self, *, tenant_id: UUID, table_session_id: UUID):
        row = await self.session.execute(
            select(
                checks.c.id.label("check_id"),
                checks.c.status.label("check_status"),
                table_sessions.c.status.label("session_status"),
            )
            .select_from(
                checks.join(
                    table_sessions,
                    (table_sessions.c.tenant_id == checks.c.tenant_id)
                    & (table_sessions.c.id == checks.c.table_session_id),
                )
            )
            .where(
                checks.c.tenant_id == tenant_id,
                checks.c.table_session_id == table_session_id,
            )
        )
        return row.mappings().first()

    async def _closure_row(self, *, tenant_id: UUID, table_session_id: UUID):
        row = await self.session.execute(
            select(session_closures).where(
                session_closures.c.tenant_id == tenant_id,
                session_closures.c.table_session_id == table_session_id,
            )
        )
        return row.mappings().first()

    async def _total_minor(self, *, tenant_id: UUID, table_session_id: UUID) -> int:
        return int(
            (
                await self.session.execute(
                    select(
                        func.coalesce(
                            func.sum(order_items.c.unit_price_minor * order_items.c.quantity),
                            0,
                        )
                    )
                    .select_from(
                        orders.join(
                            order_items,
                            (order_items.c.tenant_id == orders.c.tenant_id)
                            & (order_items.c.order_id == orders.c.id),
                        )
                    )
                    .where(
                        orders.c.tenant_id == tenant_id,
                        orders.c.table_session_id == table_session_id,
                        order_items.c.voided_at.is_(None),
                    )
                )
            ).scalar_one()
            or 0
        )

    async def _currency(self, *, tenant_id: UUID, table_session_id: UUID) -> str:
        value = (
            await self.session.execute(
                select(order_items.c.currency_code)
                .select_from(
                    orders.join(
                        order_items,
                        (order_items.c.tenant_id == orders.c.tenant_id)
                        & (order_items.c.order_id == orders.c.id),
                    )
                )
                .where(
                    orders.c.tenant_id == tenant_id,
                    orders.c.table_session_id == table_session_id,
                    order_items.c.voided_at.is_(None),
                )
                .order_by(desc(order_items.c.created_at))
                .limit(1)
            )
        ).scalar_one_or_none()
        return value or "TRY"

    async def _order_count(self, *, tenant_id: UUID, table_session_id: UUID) -> int:
        return int(
            (
                await self.session.execute(
                    select(func.count(distinct(orders.c.id))).where(
                        orders.c.tenant_id == tenant_id,
                        orders.c.table_session_id == table_session_id,
                    )
                )
            ).scalar_one()
            or 0
        )

    async def _payment_count(self, *, tenant_id: UUID, check_id: UUID) -> int:
        return int(
            (
                await self.session.execute(
                    select(func.count(payments.c.id)).where(
                        payments.c.tenant_id == tenant_id,
                        payments.c.check_id == check_id,
                        payments.c.status == "recorded",
                    )
                )
            ).scalar_one()
            or 0
        )


def require_cashier(actor: ActorContext) -> None:
    if StaffRole.CASHIER not in actor.roles:
        raise not_authorized()


def not_authorized() -> ApiError:
    return ApiError(status_code=403, code="not_authorized", message="Not authorized.")


def not_found() -> ApiError:
    return ApiError(status_code=404, code="not_found_or_hidden", message="Not found.")


def check_closed() -> ApiError:
    return ApiError(status_code=409, code="check_closed", message="Check is closed.")


def remaining_balance_not_zero() -> ApiError:
    return ApiError(
        status_code=409,
        code="remaining_balance_not_zero",
        message="Remaining balance must be zero before closing the session.",
    )


def invalid_state() -> ApiError:
    return ApiError(status_code=409, code="invalid_state", message="Invalid session state.")
