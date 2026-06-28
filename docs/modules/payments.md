# Module: Payments

## Purpose

Payments owns payment records, partial/full payment rules, payment method tracking, and payment idempotency.

In v1, payments are cashier-recorded settlement records unless an external payment provider is explicitly introduced.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Payment | Entity | create, read, void/reverse if introduced |
| Payment method | Value | cash, card, transfer, mixed if supported |
| Payment idempotency | Safety record | prevent duplicate payment records |
| Payment summary | Read model | paid amount by TableSession |

## Not Owned

- TableSession closure rules, owned by Table Session and Billing.
- Order item pricing snapshots.
- External provider settlement unless added later.
- CustomerApp payment actions.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| CashierApp / Cashier | create partial/full payment records | Cashier permission required |
| CustomerApp | read table paid/remaining summary | Fresh table presence, read-only |
| PlatformApp | no direct runtime payment operation | Support only if explicit workflow exists |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Record payment | Add payment to TableSession | CashierApp |
| List payments | Payment history/summary | CashierApp |
| Get paid amount | Billing calculation | Table Session and Billing |
| Get customer-visible summary | Read-only balance | CustomerApp |

## Internal Rules

- Partial payments reduce remaining balance but do not close TableSession.
- Full payment can enable session closure, but closure remains explicit CashierApp action.
- CustomerApp cannot create or mutate payments.
- Payment totals must be calculated server-side.
- Payment cannot exceed allowed amount unless an explicit overpayment rule exists.

## Operational Safety

- Payment creation must be idempotent.
- Payment updates must run in a transaction with billing read model updates if materialized.
- Duplicate cashier clicks must not create duplicate payments.
- External payment providers require retry, reconciliation, and compensating-action rules before use.
- Payment records and corrections must be audited.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| Payment | Payment record | tableSessionId, amount, method, cashier |
| PaymentIdempotency | Duplicate payment protection | scoped key |
| PaymentCorrection | Future reversal/void record | reason and actor |

## App Surfaces

| App | Usage |
| --- | --- |
| CashierApp | Primary payment recording |
| CustomerApp | Read-only paid/remaining summary |

## Future Service Boundary

- Own data: payments, payment idempotency, payment corrections.
- Own APIs: record payment, list payments, get paid amount.
- Published events: payment.recorded, payment.voided.
- Consumed events: table_session.closed.
- Must not leak: payment mutation to CustomerApp.

## Open Questions

- Payment methods in v1: cash, card, transfer, mixed.
- Whether external payment providers are out of scope for v1.
- Whether payment can be split by item/person or only amount.
