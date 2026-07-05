# API Contracts: Payments

Source contracts: [payments-contracts.md](payments-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Payments owns cashier-recorded payments, payment idempotency, payment history, payment voids, and customer-visible payment summary.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/cashier/checks/{checkId}/payments` | CashierApp | `payments.list_payments` | Cashier session | Path: `checkId`; query: `cursor`, `limit` | `PaymentList` | `missing_role`, `not_found_or_hidden` |
| `GET` | `/api/cashier/payments` | CashierApp | `payments.list_tenant_payments` | Cashier session | Query: `businessDay=current`, `method?`, `status?`, `cursor`, `limit` | `PaymentList` | `missing_role`, `validation_failed` |
| `POST` | `/api/cashier/checks/{checkId}/payments` | CashierApp | `payments.record_payment` | Cashier session + CSRF + `Idempotency-Key` | Body: `RecordPaymentRequest` | `PaymentResult` | `overpayment_not_allowed`, `idempotency_conflict`, `check_closed` |
| `POST` | `/api/cashier/payments/{paymentId}/void` | CashierApp | `payments.void_payment` | Cashier session + CSRF + `Idempotency-Key` | Body: `reason` | `PaymentVoidResult` | `payment_void_not_allowed`, `reason_required`, `check_closed`, `idempotency_conflict` |
| `GET` | `/api/customer/table-session/payment-summary` | CustomerApp | `payments.get_customer_visible_summary` | Customer session + fresh presence | Host/cookie-derived table session | `CustomerPaymentSummary` | `fresh_presence_required` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `payments.get_paid_amount` | Internal Settlement call. |
| `payments.get_payment_idempotency_result` | API/module idempotency replay helper. |

## Request Schemas

`RecordPaymentRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `amountMinor` | integer | yes | Must be positive and not exceed remaining balance. |
| `currency` | string | yes | Must match check currency. |
| `method` | string enum | yes | Current release non-provider method enum. |
| `note` | string | no | Cashier note; safe text only. |

The API layer computes the normalized request hash from route, check, actor, and body fields. The client must not send a trusted `requestHash`.

`VoidPaymentRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `reason` | string | yes | Required and audited. |

The API layer computes the normalized request hash from route, payment, actor, and reason. The client sends only `Idempotency-Key`, not a request hash.

## Response Schemas

`Payment` includes `paymentId`, `checkId`, `tableSessionId`, `tableLabel`, `amountMinor`, `currency`, `method`, `status`, `cashierDisplayName`, `recordedAt`, `voidedAt?`, and safe cashier note fields.

`PaymentResult` includes `payment`, updated `paidMinor`, updated `remainingMinor`, and `duplicate` when returned from compatible idempotent replay.

`PaymentVoidResult` includes voided `payment`, linked correction/audit reference, updated `paidMinor`, and updated `remainingMinor`.

`CustomerPaymentSummary` includes `paidMinor`, `remainingMinor`, `currency`, visible payment count, and last payment time when allowed by CustomerApp visibility rules.

## Idempotency

`POST /api/cashier/checks/{checkId}/payments` requires `Idempotency-Key`.

Scope the key by `tenantId + checkId + route + idempotencyKey`. Same key and same request returns the original `PaymentResult`. Same key and different request returns `409 idempotency_conflict`.

`POST /api/cashier/payments/{paymentId}/void` requires `Idempotency-Key`.

Scope the key by `tenantId + paymentId + route + idempotencyKey`. Same key and same request returns the original `PaymentVoidResult`. Same key and different request returns `409 idempotency_conflict`.
