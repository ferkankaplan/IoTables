from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import (
    audit_events,
    cashier_corrections,
    checks,
    payment_idempotency,
    payment_void_idempotency,
    payments,
)
from iotables.modules.settlement.table_session_billing import (
    TableSessionBillingService,
    require_cashier,
)
from iotables.security.context import ActorContext


@dataclass(frozen=True)
class Payment:
    payment_id: UUID
    check_id: UUID
    table_session_id: UUID
    amount_minor: int
    currency: str
    method: str
    status: str
    recorded_at: datetime
    voided_at: datetime | None

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "paymentId": str(self.payment_id),
            "checkId": str(self.check_id),
            "tableSessionId": str(self.table_session_id),
            "amountMinor": self.amount_minor,
            "currency": self.currency,
            "method": self.method,
            "status": self.status,
            "recordedAt": self.recorded_at.isoformat(),
            "voidedAt": self.voided_at.isoformat() if self.voided_at else None,
        }


@dataclass(frozen=True)
class PaymentList:
    items: tuple[Payment, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {"items": [item.as_api_payload() for item in self.items]}


@dataclass(frozen=True)
class PaymentResult:
    payment: Payment
    paid_minor: int
    remaining_minor: int
    duplicate: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "payment": self.payment.as_api_payload(),
            "paidMinor": self.paid_minor,
            "remainingMinor": self.remaining_minor,
            "duplicate": self.duplicate,
        }


@dataclass(frozen=True)
class PaymentVoidResult:
    payment: Payment
    paid_minor: int
    remaining_minor: int
    correction_id: UUID
    duplicate: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "payment": self.payment.as_api_payload(),
            "paidMinor": self.paid_minor,
            "remainingMinor": self.remaining_minor,
            "correctionId": str(self.correction_id),
            "duplicate": self.duplicate,
        }


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.billing = TableSessionBillingService(session)

    async def list_payments(self, *, actor: ActorContext, check_id: UUID) -> PaymentList:
        require_cashier(actor)
        if actor.tenant_id is None:
            raise not_authorized()
        rows = (
            (
                await self.session.execute(
                    payment_select().where(
                        payments.c.tenant_id == actor.tenant_id,
                        payments.c.check_id == check_id,
                    )
                )
            )
            .mappings()
            .all()
        )
        return PaymentList(items=tuple(to_payment(row) for row in rows))

    async def record_payment(
        self,
        *,
        actor: ActorContext,
        check_id: UUID,
        amount_minor: int,
        currency: str,
        method: str,
        idempotency_key: str,
        request_hash: str,
    ) -> PaymentResult:
        require_cashier(actor)
        if actor.tenant_id is None or actor.user_id is None:
            raise not_authorized()
        if amount_minor <= 0:
            raise validation_failed()
        if method not in {"cash", "card", "transfer"}:
            raise validation_failed()
        check_row = await self._check_row(tenant_id=actor.tenant_id, check_id=check_id)
        if check_row is None:
            raise not_found()
        if check_row["status"] != "open":
            raise check_closed()

        existing_idempotency = await self._idempotency_row(
            tenant_id=actor.tenant_id,
            check_id=check_id,
            idempotency_key=idempotency_key,
        )
        if existing_idempotency is not None:
            if existing_idempotency["request_hash"] != request_hash:
                raise idempotency_conflict()
            if existing_idempotency["status"] == "completed" and existing_idempotency["payment_id"]:
                return await self._payment_result(
                    actor=actor,
                    payment_id=existing_idempotency["payment_id"],
                    duplicate=True,
                )
            raise idempotency_conflict()

        summary = await self.billing.bill_summary_for_check(
            tenant_id=actor.tenant_id,
            check_id=check_id,
            table_session_id=check_row["table_session_id"],
        )
        if currency != summary.currency:
            raise validation_failed()
        if amount_minor > summary.remaining_minor:
            raise overpayment_not_allowed()

        now = datetime.now(UTC)
        await self.session.execute(
            insert(payment_idempotency).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                check_id=check_id,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                payment_id=None,
                status="processing",
                created_at=now,
                completed_at=None,
            )
        )
        payment_id = uuid4()
        await self.session.execute(
            insert(payments).values(
                id=payment_id,
                tenant_id=actor.tenant_id,
                check_id=check_id,
                amount_minor=amount_minor,
                currency_code=currency,
                method=method,
                status="recorded",
                cashier_user_id=actor.user_id,
                received_at=now,
                voided_at=None,
                voided_by_user_id=None,
                void_reason=None,
                created_at=now,
                updated_at=now,
            )
        )
        await self.session.execute(
            update(payment_idempotency)
            .where(
                payment_idempotency.c.tenant_id == actor.tenant_id,
                payment_idempotency.c.check_id == check_id,
                payment_idempotency.c.idempotency_key == idempotency_key,
            )
            .values(payment_id=payment_id, status="completed", completed_at=now)
        )
        await self.session.execute(
            insert(audit_events).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                actor_user_id=actor.user_id,
                action="payment.recorded",
                target_type="payment",
                target_id=str(payment_id),
                reason=None,
                metadata={
                    "checkId": str(check_id),
                    "amountMinor": amount_minor,
                    "currency": currency,
                    "method": method,
                },
                created_at=now,
            )
        )
        await self.session.commit()
        return await self._payment_result(actor=actor, payment_id=payment_id, duplicate=False)

    async def void_payment(
        self,
        *,
        actor: ActorContext,
        payment_id: UUID,
        reason: str,
        idempotency_key: str,
        request_hash: str,
    ) -> PaymentVoidResult:
        require_cashier(actor)
        if actor.tenant_id is None or actor.user_id is None:
            raise not_authorized()
        normalized_reason = reason.strip()
        if not normalized_reason:
            raise reason_required()

        payment_row = await self._payment_row(tenant_id=actor.tenant_id, payment_id=payment_id)
        if payment_row is None:
            raise not_found()
        check_row = await self._check_row(
            tenant_id=actor.tenant_id,
            check_id=payment_row["check_id"],
        )
        if check_row is None:
            raise not_found()
        if check_row["status"] != "open":
            raise check_closed()

        existing_idempotency = await self._void_idempotency_row(
            tenant_id=actor.tenant_id,
            payment_id=payment_id,
            idempotency_key=idempotency_key,
        )
        if existing_idempotency is not None:
            if existing_idempotency["request_hash"] != request_hash:
                raise idempotency_conflict()
            if existing_idempotency["status"] == "completed":
                return await self._payment_void_result(
                    actor=actor,
                    payment_id=payment_id,
                    duplicate=True,
                )
            raise idempotency_conflict()

        if payment_row["status"] != "recorded" or payment_row["voided_at"] is not None:
            raise payment_void_not_allowed()

        now = datetime.now(UTC)
        await self.session.execute(
            insert(payment_void_idempotency).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                payment_id=payment_id,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                status="processing",
                created_at=now,
                completed_at=None,
            )
        )
        await self.session.execute(
            update(payments)
            .where(
                payments.c.tenant_id == actor.tenant_id,
                payments.c.id == payment_id,
                payments.c.status == "recorded",
            )
            .values(
                status="voided",
                voided_at=now,
                voided_by_user_id=actor.user_id,
                void_reason=normalized_reason,
                updated_at=now,
            )
        )
        correction_id = uuid4()
        await self.session.execute(
            insert(cashier_corrections).values(
                id=correction_id,
                tenant_id=actor.tenant_id,
                check_id=payment_row["check_id"],
                type="payment_void",
                target_type="payment",
                target_id=payment_id,
                reason=normalized_reason,
                created_by_user_id=actor.user_id,
                created_at=now,
            )
        )
        await self.session.execute(
            update(payment_void_idempotency)
            .where(
                payment_void_idempotency.c.tenant_id == actor.tenant_id,
                payment_void_idempotency.c.payment_id == payment_id,
                payment_void_idempotency.c.idempotency_key == idempotency_key,
            )
            .values(status="completed", completed_at=now)
        )
        await self.session.execute(
            insert(audit_events).values(
                id=uuid4(),
                tenant_id=actor.tenant_id,
                actor_user_id=actor.user_id,
                action="payment.voided",
                target_type="payment",
                target_id=str(payment_id),
                reason=normalized_reason,
                metadata={
                    "checkId": str(payment_row["check_id"]),
                    "correctionId": str(correction_id),
                    "amountMinor": payment_row["amount_minor"],
                },
                created_at=now,
            )
        )
        await self.session.commit()
        return await self._payment_void_result(
            actor=actor,
            payment_id=payment_id,
            duplicate=False,
        )

    async def _payment_result(
        self,
        *,
        actor: ActorContext,
        payment_id: UUID,
        duplicate: bool,
    ) -> PaymentResult:
        if actor.tenant_id is None:
            raise not_authorized()
        row = await self._payment_row(tenant_id=actor.tenant_id, payment_id=payment_id)
        if row is None:
            raise not_found()
        summary = await self.billing.bill_summary_for_check(
            tenant_id=actor.tenant_id,
            check_id=row["check_id"],
            table_session_id=row["table_session_id"],
        )
        return PaymentResult(
            payment=to_payment(row),
            paid_minor=summary.paid_minor,
            remaining_minor=summary.remaining_minor,
            duplicate=duplicate,
        )

    async def _payment_void_result(
        self,
        *,
        actor: ActorContext,
        payment_id: UUID,
        duplicate: bool,
    ) -> PaymentVoidResult:
        if actor.tenant_id is None:
            raise not_authorized()
        row = await self._payment_row(tenant_id=actor.tenant_id, payment_id=payment_id)
        if row is None:
            raise not_found()
        correction_id = await self._payment_void_correction_id(
            tenant_id=actor.tenant_id,
            check_id=row["check_id"],
            payment_id=payment_id,
        )
        if correction_id is None:
            raise not_found()
        summary = await self.billing.bill_summary_for_check(
            tenant_id=actor.tenant_id,
            check_id=row["check_id"],
            table_session_id=row["table_session_id"],
        )
        return PaymentVoidResult(
            payment=to_payment(row),
            paid_minor=summary.paid_minor,
            remaining_minor=summary.remaining_minor,
            correction_id=correction_id,
            duplicate=duplicate,
        )

    async def _check_row(self, *, tenant_id: UUID, check_id: UUID):
        row = await self.session.execute(
            select(checks).where(checks.c.tenant_id == tenant_id, checks.c.id == check_id)
        )
        return row.mappings().first()

    async def _void_idempotency_row(
        self,
        *,
        tenant_id: UUID,
        payment_id: UUID,
        idempotency_key: str,
    ):
        row = await self.session.execute(
            select(payment_void_idempotency).where(
                payment_void_idempotency.c.tenant_id == tenant_id,
                payment_void_idempotency.c.payment_id == payment_id,
                payment_void_idempotency.c.idempotency_key == idempotency_key,
            )
        )
        return row.mappings().first()

    async def _payment_void_correction_id(
        self,
        *,
        tenant_id: UUID,
        check_id: UUID,
        payment_id: UUID,
    ) -> UUID | None:
        return (
            await self.session.execute(
                select(cashier_corrections.c.id)
                .where(
                    cashier_corrections.c.tenant_id == tenant_id,
                    cashier_corrections.c.check_id == check_id,
                    cashier_corrections.c.type == "payment_void",
                    cashier_corrections.c.target_type == "payment",
                    cashier_corrections.c.target_id == payment_id,
                )
                .order_by(cashier_corrections.c.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def _payment_row(self, *, tenant_id: UUID, payment_id: UUID):
        row = await self.session.execute(
            payment_select().where(payments.c.tenant_id == tenant_id, payments.c.id == payment_id)
        )
        return row.mappings().first()

    async def _idempotency_row(
        self,
        *,
        tenant_id: UUID,
        check_id: UUID,
        idempotency_key: str,
    ):
        row = await self.session.execute(
            select(payment_idempotency).where(
                payment_idempotency.c.tenant_id == tenant_id,
                payment_idempotency.c.check_id == check_id,
                payment_idempotency.c.idempotency_key == idempotency_key,
            )
        )
        return row.mappings().first()


def payment_select():
    return select(
        payments.c.id.label("payment_id"),
        payments.c.check_id,
        checks.c.table_session_id,
        payments.c.amount_minor,
        payments.c.currency_code,
        payments.c.method,
        payments.c.status,
        payments.c.received_at,
        payments.c.voided_at,
    ).select_from(
        payments.join(
            checks,
            (checks.c.tenant_id == payments.c.tenant_id) & (checks.c.id == payments.c.check_id),
        )
    )


def to_payment(row: Any) -> Payment:
    return Payment(
        payment_id=row["payment_id"],
        check_id=row["check_id"],
        table_session_id=row["table_session_id"],
        amount_minor=row["amount_minor"],
        currency=row["currency_code"],
        method=row["method"],
        status=row["status"],
        recorded_at=row["received_at"],
        voided_at=row["voided_at"],
    )


def not_authorized() -> ApiError:
    return ApiError(status_code=403, code="not_authorized", message="Not authorized.")


def not_found() -> ApiError:
    return ApiError(status_code=404, code="not_found_or_hidden", message="Not found.")


def check_closed() -> ApiError:
    return ApiError(status_code=409, code="check_closed", message="Check is closed.")


def overpayment_not_allowed() -> ApiError:
    return ApiError(
        status_code=409,
        code="overpayment_not_allowed",
        message="Payment amount exceeds remaining balance.",
    )


def payment_void_not_allowed() -> ApiError:
    return ApiError(
        status_code=409,
        code="payment_void_not_allowed",
        message="Payment cannot be voided.",
    )


def reason_required() -> ApiError:
    return ApiError(status_code=422, code="reason_required", message="Reason is required.")


def idempotency_conflict() -> ApiError:
    return ApiError(
        status_code=409,
        code="idempotency_conflict",
        message="Idempotency key was already used for a different request.",
    )


def validation_failed() -> ApiError:
    return ApiError(status_code=422, code="validation_failed", message="Validation failed.")
