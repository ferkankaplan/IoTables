from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.cashier import (
    get_customer_ordering_service,
    get_payment_service,
    get_table_presence_service,
    get_table_session_billing_service,
)
from iotables.main import create_app
from iotables.modules.ordering.customer_ordering import (
    CashierOrder,
    CashierOrderItem,
    CashierOrderList,
)
from iotables.modules.ordering.table_presence import QrTokenPayload
from iotables.modules.settlement.payments import (
    Payment,
    PaymentList,
    PaymentResult,
    PaymentVoidResult,
)
from iotables.modules.settlement.table_session_billing import (
    ActiveTableSession,
    BillSummary,
    CashierTableState,
    CashierVenueBoard,
    ClosedTableSession,
)
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole

TENANT_ID = UUID("33333333-3333-3333-3333-333333333333")
USER_ID = UUID("44444444-4444-4444-4444-444444444444")
HALL_ID = UUID("55555555-5555-5555-5555-555555555555")
TABLE_ID = UUID("66666666-6666-6666-6666-666666666666")
TABLE_SESSION_ID = UUID("77777777-7777-7777-7777-777777777777")
CHECK_ID = UUID("88888888-8888-8888-8888-888888888888")
PAYMENT_ID = UUID("99999999-9999-9999-9999-999999999999")
ORDER_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
ORDER_ITEM_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


class FakeSessionResolver:
    def __init__(self, actor: ActorContext | None) -> None:
        self.actor = actor

    async def resolve(self, session_token: str) -> ActorContext | None:
        return self.actor if session_token == "cashier-token" else None


class FakeBillingService:
    def __init__(self) -> None:
        self.close_args: dict[str, object] | None = None
        self.venue_board_args: dict[str, object] | None = None

    async def venue_board(
        self, *, actor: ActorContext, include_virtual_test_tables: bool = False
    ) -> CashierVenueBoard:
        self.venue_board_args = {
            "actor": actor,
            "include_virtual_test_tables": include_virtual_test_tables,
        }
        return CashierVenueBoard(
            tables=(
                CashierTableState(
                    table_id=TABLE_ID,
                    hall_id=HALL_ID,
                    table_label="Masa 001",
                    hall_label="Salon 1",
                    mode="physical",
                    table_session_id=TABLE_SESSION_ID,
                    check_id=CHECK_ID,
                    status="occupied",
                    opened_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
                    total_minor=1000,
                    paid_minor=400,
                    remaining_minor=600,
                ),
            ),
            derived_at=datetime(2026, 7, 3, 12, 10, tzinfo=UTC),
        )

    async def get_active_table_session(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
    ) -> ActiveTableSession:
        _ = actor
        return ActiveTableSession(
            table_session_id=TABLE_SESSION_ID,
            table_id=table_id,
            hall_id=HALL_ID,
            check_id=CHECK_ID,
            status="open",
            opened_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
            table_label="Masa 001",
            hall_label="Salon 1",
        )

    async def get_bill_summary(
        self,
        *,
        actor: ActorContext,
        table_session_id: UUID,
    ) -> BillSummary:
        _ = actor
        return BillSummary(
            check_id=CHECK_ID,
            table_session_id=table_session_id,
            total_minor=1000,
            paid_minor=400,
            remaining_minor=600,
            currency="TRY",
            order_count=2,
            payment_count=1,
        )

    async def close_session(
        self,
        *,
        actor: ActorContext,
        table_session_id: UUID,
        reason: str | None,
    ) -> ClosedTableSession:
        self.close_args = {"actor": actor, "table_session_id": table_session_id, "reason": reason}
        return ClosedTableSession(
            table_session_id=table_session_id,
            check_id=CHECK_ID,
            closed_at=datetime(2026, 7, 3, 12, 20, tzinfo=UTC),
            status="closed",
        )


class FakePaymentService:
    def __init__(self) -> None:
        self.record_args: dict[str, object] | None = None
        self.void_args: dict[str, object] | None = None

    async def list_payments(self, *, actor: ActorContext, check_id: UUID) -> PaymentList:
        _ = actor
        return PaymentList(items=(make_payment(check_id=check_id),))

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
        self.record_args = {
            "actor": actor,
            "check_id": check_id,
            "amount_minor": amount_minor,
            "currency": currency,
            "method": method,
            "idempotency_key": idempotency_key,
            "request_hash": request_hash,
        }
        return PaymentResult(
            payment=make_payment(check_id=check_id, amount_minor=amount_minor),
            paid_minor=amount_minor,
            remaining_minor=0,
            duplicate=False,
        )

    async def void_payment(
        self,
        *,
        actor: ActorContext,
        payment_id: UUID,
        reason: str,
        idempotency_key: str,
        request_hash: str,
    ) -> PaymentVoidResult:
        self.void_args = {
            "actor": actor,
            "payment_id": payment_id,
            "reason": reason,
            "idempotency_key": idempotency_key,
            "request_hash": request_hash,
        }
        return PaymentVoidResult(
            payment=make_payment(check_id=CHECK_ID, status="voided"),
            paid_minor=0,
            remaining_minor=600,
            correction_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            duplicate=False,
        )


class FakeTablePresenceService:
    def __init__(self) -> None:
        self.preview_args: dict[str, object] | None = None

    async def issue_virtual_table_qr_preview(
        self, *, actor: ActorContext, table_id: UUID
    ) -> QrTokenPayload:
        self.preview_args = {"actor": actor, "table_id": table_id}
        return QrTokenPayload(
            qr_token="preview-token",
            expires_at=datetime(2026, 7, 3, 12, 11, tzinfo=UTC),
            refresh_after_seconds=60,
        )


class FakeCustomerOrderingService:
    def __init__(self) -> None:
        self.args: dict[str, object] | None = None

    async def list_table_orders(
        self,
        *,
        actor: ActorContext,
        table_session_id: UUID,
    ) -> CashierOrderList:
        self.args = {"actor": actor, "table_session_id": table_session_id}
        return CashierOrderList(
            items=(
                CashierOrder(
                    order_id=ORDER_ID,
                    table_session_id=table_session_id,
                    submitted_at=datetime(2026, 7, 3, 12, 3, tzinfo=UTC),
                    items=(
                        CashierOrderItem(
                            order_item_id=ORDER_ITEM_ID,
                            name="Americano",
                            variant_name="Standart",
                            quantity=2,
                            unit_price_minor=100,
                            currency="TRY",
                            note=None,
                            voided=False,
                        ),
                    ),
                ),
            )
        )


def make_payment(*, check_id: UUID, amount_minor: int = 400, status: str = "recorded") -> Payment:
    return Payment(
        payment_id=PAYMENT_ID,
        check_id=check_id,
        table_session_id=TABLE_SESSION_ID,
        amount_minor=amount_minor,
        currency="TRY",
        method="cash",
        status=status,
        recorded_at=datetime(2026, 7, 3, 12, 10, tzinfo=UTC),
        voided_at=datetime(2026, 7, 3, 12, 15, tzinfo=UTC) if status == "voided" else None,
    )


def make_actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.TENANT_USER,
        app_scope=AppScope.CASHIER,
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        roles=frozenset({StaffRole.CASHIER}),
    )


def test_cashier_board_and_bill_summary_use_cashier_scope() -> None:
    service = FakeBillingService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_table_session_billing_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "cashier-token")

    board = client.get("/api/cashier/venue/board")
    active = client.get(f"/api/cashier/tables/{TABLE_ID}/active-session")
    summary = client.get(f"/api/cashier/table-sessions/{TABLE_SESSION_ID}/bill-summary")

    assert board.status_code == 200
    assert board.json()["tables"][0]["remainingMinor"] == 600
    assert active.status_code == 200
    assert active.json()["checkId"] == str(CHECK_ID)
    assert summary.status_code == 200
    assert summary.json()["currency"] == "TRY"


def test_cashier_board_can_include_virtual_test_tables_explicitly() -> None:
    service = FakeBillingService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_table_session_billing_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "cashier-token")

    response = client.get("/api/cashier/venue/board?includeVirtualTestTables=true")

    assert response.status_code == 200
    assert service.venue_board_args is not None
    assert service.venue_board_args["include_virtual_test_tables"] is True


def test_cashier_virtual_table_qr_preview_requires_csrf_and_binds_actor() -> None:
    service = FakeTablePresenceService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_table_presence_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "cashier-token")

    missing_csrf = client.post(f"/api/cashier/virtual-tables/{TABLE_ID}/qr-preview")
    preview = client.post(
        f"/api/cashier/virtual-tables/{TABLE_ID}/qr-preview",
        headers={"X-CSRF-Token": "csrf"},
    )

    assert missing_csrf.status_code == 403
    assert preview.status_code == 200
    assert preview.json()["qrToken"] == "preview-token"
    assert service.preview_args is not None
    assert service.preview_args["table_id"] == TABLE_ID
    assert service.preview_args["actor"] == make_actor()


def test_cashier_table_session_orders_use_ordering_contract() -> None:
    service = FakeCustomerOrderingService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_customer_ordering_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "cashier-token")

    response = client.get(f"/api/cashier/table-sessions/{TABLE_SESSION_ID}/orders")

    assert response.status_code == 200
    assert response.json()["items"][0]["items"][0]["name"] == "Americano"
    assert service.args is not None
    assert service.args["table_session_id"] == TABLE_SESSION_ID


def test_cashier_record_payment_requires_csrf_and_idempotency_key() -> None:
    service = FakePaymentService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_payment_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "cashier-token")
    payload = {"amountMinor": 600, "currency": "TRY", "method": "cash"}

    missing_csrf = client.post(
        f"/api/cashier/checks/{CHECK_ID}/payments",
        headers={"Idempotency-Key": "pay-1"},
        json=payload,
    )
    missing_key = client.post(
        f"/api/cashier/checks/{CHECK_ID}/payments",
        headers={"X-CSRF-Token": "csrf"},
        json=payload,
    )
    paid = client.post(
        f"/api/cashier/checks/{CHECK_ID}/payments",
        headers={"X-CSRF-Token": "csrf", "Idempotency-Key": "pay-1"},
        json=payload,
    )

    assert missing_csrf.status_code == 403
    assert missing_key.status_code == 400
    assert paid.status_code == 200
    assert paid.json()["payment"]["amountMinor"] == 600
    assert service.record_args is not None
    assert service.record_args["idempotency_key"] == "pay-1"
    assert isinstance(service.record_args["request_hash"], str)
    assert len(service.record_args["request_hash"]) == 64


def test_cashier_close_session_requires_csrf_and_binds_actor() -> None:
    service = FakeBillingService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_table_session_billing_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "cashier-token")

    missing_csrf = client.post(f"/api/cashier/table-sessions/{TABLE_SESSION_ID}/close")
    closed = client.post(
        f"/api/cashier/table-sessions/{TABLE_SESSION_ID}/close",
        headers={"X-CSRF-Token": "csrf"},
        json={"reason": "ödendi"},
    )

    assert missing_csrf.status_code == 403
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert service.close_args is not None
    assert service.close_args["table_session_id"] == TABLE_SESSION_ID
    assert service.close_args["reason"] == "ödendi"


def test_cashier_void_payment_requires_csrf_idempotency_and_reason() -> None:
    service = FakePaymentService()
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(make_actor())
    app.dependency_overrides[get_payment_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("iotables_session", "cashier-token")

    missing_csrf = client.post(
        f"/api/cashier/payments/{PAYMENT_ID}/void",
        headers={"Idempotency-Key": "void-1"},
        json={"reason": "hatalı ödeme"},
    )
    missing_key = client.post(
        f"/api/cashier/payments/{PAYMENT_ID}/void",
        headers={"X-CSRF-Token": "csrf"},
        json={"reason": "hatalı ödeme"},
    )
    voided = client.post(
        f"/api/cashier/payments/{PAYMENT_ID}/void",
        headers={"X-CSRF-Token": "csrf", "Idempotency-Key": "void-1"},
        json={"reason": "hatalı ödeme"},
    )

    assert missing_csrf.status_code == 403
    assert missing_key.status_code == 400
    assert voided.status_code == 200
    assert voided.json()["payment"]["status"] == "voided"
    assert voided.json()["correctionId"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert service.void_args is not None
    assert service.void_args["payment_id"] == PAYMENT_ID
    assert service.void_args["reason"] == "hatalı ödeme"
    assert service.void_args["idempotency_key"] == "void-1"
    assert isinstance(service.void_args["request_hash"], str)
    assert len(service.void_args["request_hash"]) == 64
