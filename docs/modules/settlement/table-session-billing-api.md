# API Contracts: Table Session and Billing

Source contracts: [table-session-billing-contracts.md](table-session-billing-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Table Session and Billing owns active table sessions, v1 single Check/Adisyon, bill summary, cashier corrections, and close-session rules.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/cashier/tables/{tableId}/active-session` | CashierApp | `table_session_billing.get_active_table_session` | Cashier session | Path: `tableId` | `ActiveTableSession` | `missing_role`, `not_found_or_hidden` |
| `GET` | `/api/v1/customer/table-session` | CustomerApp | `table_session_billing.get_active_table_session` | Customer session + fresh presence | Host/cookie-derived table | `ActiveTableSession` | `fresh_presence_required` |
| `GET` | `/api/v1/cashier/table-sessions/{tableSessionId}/bill-summary` | CashierApp | `table_session_billing.get_bill_summary` | Cashier session | Path: `tableSessionId` | `BillSummary` | `missing_role`, `not_found_or_hidden` |
| `GET` | `/api/v1/customer/table-session/bill-summary` | CustomerApp | `table_session_billing.get_bill_summary` | Customer session + fresh presence | Host/cookie-derived table session | `CustomerBillSummary` | `fresh_presence_required` |
| `GET` | `/api/v1/cashier/checks/{checkId}` | CashierApp | `table_session_billing.get_check` | Cashier session | Path: `checkId` | `CheckDetail` | `missing_role`, `not_found_or_hidden` |
| `GET` | `/api/v1/cashier/checks/{checkId}/corrections` | CashierApp | `table_session_billing.list_cashier_corrections` | Cashier session | Path: `checkId`; query: `cursor`, `limit` | `CashierCorrectionList` | `missing_role` |
| `POST` | `/api/v1/cashier/checks/{checkId}/corrections` | CashierApp | `table_session_billing.record_cashier_correction` | Cashier session + CSRF + `Idempotency-Key` | Body: `CashierCorrectionRequest` | `CashierCorrectionResult` | `correction_not_allowed`, `reason_required`, `check_closed`, `idempotency_conflict` |
| `POST` | `/api/v1/cashier/table-sessions/{tableSessionId}/close` | CashierApp | `table_session_billing.close_session` | Cashier session + CSRF | Body: `reason?` | `ClosedTableSession` | `remaining_balance_not_zero`, `check_closed`, `invalid_state` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `table_session_billing.open_session_check_if_needed` | Called by Customer Ordering inside accepted order submission. |

## Request Schemas

`CashierCorrectionRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `type` | string enum | yes | Supported v1 correction type. |
| `targetType` | string enum | yes | Payment/order/check target type. |
| `targetId` | string | yes | Target record. |
| `reason` | string | yes | Required and audited. |

The API layer computes the normalized request hash from route, check, actor, correction type, target, and reason. The client sends only `Idempotency-Key`, not a request hash.

`CloseTableSessionRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `reason` | string | no | Optional close note unless policy later requires it. |

## Response Schemas

`ActiveTableSession` includes `tableSessionId`, `tableId`, `hallId`, `checkId`, `status`, `openedAt`, and optional display labels.

`BillSummary` includes `checkId`, `tableSessionId`, `totalMinor`, `paidMinor`, `remainingMinor`, `currency`, `orderCount`, `paymentCount`, and cashier-visible correction indicators.

`CustomerBillSummary` includes server-calculated totals, paid/remaining amount, currency, order/payment summary, and customer-visible timestamps. It must not expose cashier-only correction internals.

`CashierCorrectionResult` returns the correction record and updated `BillSummary`.

## Idempotency

Cashier correction requires `Idempotency-Key`. Same key and same request returns the original `CashierCorrectionResult`; same key with different request returns `409 idempotency_conflict`.

Close-session does not require `Idempotency-Key` in v1. It is naturally idempotent through TableSession/Check state, the unique `SessionClosure` record, and server-side balance recomputation. A duplicate compatible close returns the current `ClosedTableSession`; a stale or incompatible close fails without mutation.
