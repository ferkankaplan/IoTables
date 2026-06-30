# Module: Payments

## Purpose

Payments owns payment records, partial/full payment rules, payment method tracking, payment idempotency, and non-provider payment void records.

In v1, payments are cashier-recorded settlement records unless an external payment provider is explicitly introduced.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Payment | Entity | create, read, void when v1 rules allow |
| Payment method | Value | cash, card, transfer |
| Payment idempotency | Safety record | prevent duplicate payment records |
| Payment void idempotency | Safety record | prevent duplicate payment void commands |
| Payment summary | Read model | paid amount by Check |

## Not Owned

- TableSession and Check closure rules, owned by Table Session and Billing.
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
| Record payment | Add payment to Check/Adisyon | CashierApp |
| List check payments | Payment history for one Check/Adisyon | CashierApp |
| List tenant payments | Current business-day payment history | CashierApp |
| Get paid amount | Billing calculation | Table Session and Billing |
| Get customer-visible summary | Read-only balance | CustomerApp |
| Void payment | Void a non-provider payment on an open Check | CashierApp |

## Internal Rules

- Partial payments reduce remaining balance but do not close TableSession.
- Full payment can enable session closure, but closure remains explicit CashierApp action.
- V1 payment methods are `cash`, `card`, and `transfer`.
- Mixed payment is represented by multiple Payment records, not a `mixed` enum value.
- V1 payment splitting is amount-based only; item/person-level settlement is out of scope.
- External payment providers are out of scope for v1.
- CustomerApp cannot create or mutate payments.
- Payment totals must be calculated server-side.
- Payment cannot exceed the current remaining balance in v1.
- Payments attach to the single Check/Adisyon in v1.
- Payment void is allowed only while the Check is open and only for non-provider payments.
- Refunds after session closure are out of v1.

## Operational Safety

- Payment creation must be idempotent.
- Payment updates must run in a transaction with billing read model updates if materialized.
- Duplicate cashier clicks must not create duplicate payments.
- Payment void must be idempotent and reason-required.
- External payment providers require retry, reconciliation, and compensating-action rules before use.
- Payment records and corrections must be audited.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| Payment | recorded -> voided | tenant, check, amount, method, status, cashier, receivedAt, void fields | Amount positive; cannot exceed remaining balance in v1; CustomerApp cannot create/mutate payments; provider payments are out of v1 | Preserve permanently; void instead of deleting |
| PaymentIdempotency | processing -> completed / failed | tenant, check, idempotencyKey, paymentId, requestHash/status if needed | Unique by tenant + check + idempotencyKey; duplicate clicks/retries return original payment result | Retain long enough to cover cashier/network retries and audit payment safety |
| PaymentVoidIdempotency | processing -> completed / failed | tenant, payment, idempotencyKey, requestHash, status, completedAt | Unique by tenant + payment + idempotencyKey; duplicate compatible void returns original void result | Retain with payment audit history |
| PaymentVoid | created or represented by Payment void fields | tenant, payment, reason, actor, voidedAt | Allowed only on open Check and only for non-provider payments in v1; reason required | Append-only or immutable void fields; never erase original payment |

## App Surfaces

| App | Usage |
| --- | --- |
| CashierApp | Primary payment recording |
| CustomerApp | Read-only paid/remaining summary |

## Future Service Boundary

- Own data: payments, payment idempotency, payment void state.
- Own APIs: record payment, list check payments, list tenant payments, get paid amount, void payment.
- Published events: payment.recorded, payment.voided.
- Consumed events: table_session.closed.
- Must not leak: payment mutation to CustomerApp.

## Open Questions

None currently.
