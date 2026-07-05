import hashlib
import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.session import get_database_session
from iotables.modules.ordering.customer_ordering import CustomerOrderingService
from iotables.modules.settlement.payments import PaymentService
from iotables.modules.settlement.table_session_billing import TableSessionBillingService
from iotables.security.context import ActorContext, AppScope
from iotables.security.dependencies import require_app_scope, require_csrf_token

CASHIER_SCOPE_DEP = Depends(require_app_scope(AppScope.CASHIER))
CSRF_DEP = Depends(require_csrf_token)

router = APIRouter(prefix="/cashier", tags=["Cashier"])


class CashierTableStateResponse(BaseModel):
    table_id: str = Field(alias="tableId")
    hall_id: str = Field(alias="hallId")
    table_label: str = Field(alias="tableLabel")
    hall_label: str = Field(alias="hallLabel")
    table_session_id: str | None = Field(alias="tableSessionId")
    check_id: str | None = Field(alias="checkId")
    status: str
    opened_at: str | None = Field(alias="openedAt")
    total_minor: int = Field(alias="totalMinor")
    paid_minor: int = Field(alias="paidMinor")
    remaining_minor: int = Field(alias="remainingMinor")


class CashierVenueBoardResponse(BaseModel):
    tables: list[CashierTableStateResponse]
    derived_at: str = Field(alias="derivedAt")


class ActiveTableSessionResponse(BaseModel):
    table_session_id: str = Field(alias="tableSessionId")
    table_id: str = Field(alias="tableId")
    hall_id: str = Field(alias="hallId")
    check_id: str = Field(alias="checkId")
    status: str
    opened_at: str = Field(alias="openedAt")
    table_label: str = Field(alias="tableLabel")
    hall_label: str = Field(alias="hallLabel")


class BillSummaryResponse(BaseModel):
    check_id: str = Field(alias="checkId")
    table_session_id: str = Field(alias="tableSessionId")
    total_minor: int = Field(alias="totalMinor")
    paid_minor: int = Field(alias="paidMinor")
    remaining_minor: int = Field(alias="remainingMinor")
    currency: str
    order_count: int = Field(alias="orderCount")
    payment_count: int = Field(alias="paymentCount")


class CloseTableSessionRequest(BaseModel):
    reason: str | None = None


class ClosedTableSessionResponse(BaseModel):
    table_session_id: str = Field(alias="tableSessionId")
    check_id: str = Field(alias="checkId")
    closed_at: str = Field(alias="closedAt")
    status: str


class PaymentResponse(BaseModel):
    payment_id: str = Field(alias="paymentId")
    check_id: str = Field(alias="checkId")
    table_session_id: str = Field(alias="tableSessionId")
    amount_minor: int = Field(alias="amountMinor")
    currency: str
    method: str
    status: str
    recorded_at: str = Field(alias="recordedAt")
    voided_at: str | None = Field(alias="voidedAt")


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]


class RecordPaymentRequest(BaseModel):
    amount_minor: int = Field(alias="amountMinor", gt=0)
    currency: str
    method: str
    note: str | None = None


class PaymentResultResponse(BaseModel):
    payment: PaymentResponse
    paid_minor: int = Field(alias="paidMinor")
    remaining_minor: int = Field(alias="remainingMinor")
    duplicate: bool


class VoidPaymentRequest(BaseModel):
    reason: str = Field(min_length=1)


class PaymentVoidResultResponse(BaseModel):
    payment: PaymentResponse
    paid_minor: int = Field(alias="paidMinor")
    remaining_minor: int = Field(alias="remainingMinor")
    correction_id: str = Field(alias="correctionId")
    duplicate: bool


class CashierOrderItemResponse(BaseModel):
    order_item_id: str = Field(alias="orderItemId")
    name: str
    variant_name: str = Field(alias="variantName")
    quantity: int
    unit_price_minor: int = Field(alias="unitPriceMinor")
    currency: str
    note: str | None
    voided: bool


class CashierOrderResponse(BaseModel):
    order_id: str = Field(alias="orderId")
    table_session_id: str = Field(alias="tableSessionId")
    submitted_at: str = Field(alias="submittedAt")
    items: list[CashierOrderItemResponse]


class CashierOrderListResponse(BaseModel):
    items: list[CashierOrderResponse]


def get_table_session_billing_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TableSessionBillingService:
    return TableSessionBillingService(session)


def get_payment_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> PaymentService:
    return PaymentService(session)


def get_customer_ordering_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> CustomerOrderingService:
    return CustomerOrderingService(session)


@router.get("/venue/board", response_model=CashierVenueBoardResponse)
async def venue_board(
    actor: Annotated[ActorContext, CASHIER_SCOPE_DEP],
    service: Annotated[TableSessionBillingService, Depends(get_table_session_billing_service)],
) -> dict[str, Any]:
    return (await service.venue_board(actor=actor)).as_api_payload()


@router.get("/tables/{table_id}/active-session", response_model=ActiveTableSessionResponse)
async def active_table_session(
    table_id: UUID,
    actor: Annotated[ActorContext, CASHIER_SCOPE_DEP],
    service: Annotated[TableSessionBillingService, Depends(get_table_session_billing_service)],
) -> dict[str, Any]:
    return (await service.get_active_table_session(actor=actor, table_id=table_id)).as_api_payload()


@router.get("/table-sessions/{table_session_id}/bill-summary", response_model=BillSummaryResponse)
async def bill_summary(
    table_session_id: UUID,
    actor: Annotated[ActorContext, CASHIER_SCOPE_DEP],
    service: Annotated[TableSessionBillingService, Depends(get_table_session_billing_service)],
) -> dict[str, Any]:
    return (
        await service.get_bill_summary(actor=actor, table_session_id=table_session_id)
    ).as_api_payload()


@router.get("/table-sessions/{table_session_id}/orders", response_model=CashierOrderListResponse)
async def table_session_orders(
    table_session_id: UUID,
    actor: Annotated[ActorContext, CASHIER_SCOPE_DEP],
    service: Annotated[CustomerOrderingService, Depends(get_customer_ordering_service)],
) -> dict[str, Any]:
    return (
        await service.list_table_orders(actor=actor, table_session_id=table_session_id)
    ).as_api_payload()


@router.post(
    "/payments/{payment_id}/void",
    response_model=PaymentVoidResultResponse,
    dependencies=[CSRF_DEP],
)
async def void_payment(
    payment_id: UUID,
    payload: VoidPaymentRequest,
    actor: Annotated[ActorContext, CASHIER_SCOPE_DEP],
    service: Annotated[PaymentService, Depends(get_payment_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    normalized_key = validate_idempotency_key(idempotency_key)
    return (
        await service.void_payment(
            actor=actor,
            payment_id=payment_id,
            reason=payload.reason,
            idempotency_key=normalized_key,
            request_hash=payment_void_request_hash(
                actor=actor,
                payment_id=payment_id,
                payload=payload,
            ),
        )
    ).as_api_payload()


@router.post(
    "/table-sessions/{table_session_id}/close",
    response_model=ClosedTableSessionResponse,
    dependencies=[CSRF_DEP],
)
async def close_table_session(
    table_session_id: UUID,
    payload: CloseTableSessionRequest,
    actor: Annotated[ActorContext, CASHIER_SCOPE_DEP],
    service: Annotated[TableSessionBillingService, Depends(get_table_session_billing_service)],
) -> dict[str, Any]:
    return (
        await service.close_session(
            actor=actor,
            table_session_id=table_session_id,
            reason=payload.reason,
        )
    ).as_api_payload()


@router.get("/checks/{check_id}/payments", response_model=PaymentListResponse)
async def list_payments(
    check_id: UUID,
    actor: Annotated[ActorContext, CASHIER_SCOPE_DEP],
    service: Annotated[PaymentService, Depends(get_payment_service)],
) -> dict[str, Any]:
    return (await service.list_payments(actor=actor, check_id=check_id)).as_api_payload()


@router.post(
    "/checks/{check_id}/payments",
    response_model=PaymentResultResponse,
    dependencies=[CSRF_DEP],
)
async def record_payment(
    check_id: UUID,
    payload: RecordPaymentRequest,
    actor: Annotated[ActorContext, CASHIER_SCOPE_DEP],
    service: Annotated[PaymentService, Depends(get_payment_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    normalized_key = validate_idempotency_key(idempotency_key)
    return (
        await service.record_payment(
            actor=actor,
            check_id=check_id,
            amount_minor=payload.amount_minor,
            currency=payload.currency,
            method=payload.method,
            idempotency_key=normalized_key,
            request_hash=payment_request_hash(actor=actor, check_id=check_id, payload=payload),
        )
    ).as_api_payload()


def validate_idempotency_key(idempotency_key: str | None) -> str:
    if idempotency_key is None or not idempotency_key.strip():
        raise ApiError(
            status_code=400,
            code="idempotency_key_required",
            message="Idempotency-Key header is required.",
        )
    return idempotency_key.strip()


def payment_request_hash(
    *,
    actor: ActorContext,
    check_id: UUID,
    payload: RecordPaymentRequest,
) -> str:
    normalized_payload = {
        "actorUserId": str(actor.user_id),
        "tenantId": str(actor.tenant_id),
        "route": "POST /api/cashier/checks/{checkId}/payments",
        "checkId": str(check_id),
        "amountMinor": payload.amount_minor,
        "currency": payload.currency,
        "method": payload.method,
        "note": payload.note,
    }
    encoded = json.dumps(normalized_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def payment_void_request_hash(
    *,
    actor: ActorContext,
    payment_id: UUID,
    payload: VoidPaymentRequest,
) -> str:
    normalized_payload = {
        "actorUserId": str(actor.user_id),
        "tenantId": str(actor.tenant_id),
        "route": "POST /api/cashier/payments/{paymentId}/void",
        "paymentId": str(payment_id),
        "reason": payload.reason.strip(),
    }
    encoded = json.dumps(normalized_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
