# Module: Table Session and Billing

## Purpose

Table Session and Billing owns the table-based operational/billing session.

It groups all accepted orders for a table until CashierApp closes the session. It calculates totals, paid amount, and remaining balance from billable records.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| TableSession | Entity | open, read, close |
| Active table session constraint | Invariant | one active session per tenant/table |
| Bill summary | Read model/calculation | total, paid, remaining |
| Session closure rule | State transition | close only when settlement rules allow |

## Not Owned

- Customer cart.
- QR token redemption.
- Menu pricing definitions.
- Payment method execution.
- Station preparation.
- Service delivery.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| CustomerApp | Read active TableSession orders and bill summary | Requires fresh table presence; read-only |
| CashierApp | Read session, receive payment through Payments, close session | Cashier permission required |
| Customer Ordering | Open/select active TableSession during order submission | Transactional command only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Get active table session | Attach/read current table session | CustomerApp, CashierApp, Customer Ordering |
| Open session if needed | First accepted order creates session | Customer Ordering |
| Get bill summary | Show totals and balance | CustomerApp, CashierApp |
| Close session | End table session after settlement | CashierApp |

## Internal Rules

- TableSession is table-based, not customer-based.
- One active TableSession may exist per tenant/table.
- First accepted order opens a TableSession when none exists.
- Closed TableSession cannot accept new orders or payments except explicit recovery.
- CustomerApp can read bill summary but cannot settle, discount, or close.
- CashierApp performs settlement and closure.

## Operational Safety

- Active TableSession creation must be concurrency-safe.
- Database must enforce one active session per tenant/table.
- Session closure must be idempotent.
- Bill summary must be calculated server-side from order item price snapshots, corrections, and payment records.
- Session must not close with remaining balance unless an explicit approved settlement rule exists.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| TableSession | Active/closed table session | tenant, table, status, openedAt, closedAt |
| BillSummary | Calculated/read model | total, paid, remaining |
| SessionClosure | Closure event/state | cashier, timestamp, reason when needed |

## App Surfaces

| App | Usage |
| --- | --- |
| CustomerApp | Reads table orders and bill summary with fresh presence |
| CashierApp | Primary settlement and session closure surface |

## Future Service Boundary

- Own data: table sessions, session state, billing read models.
- Own APIs: active session lookup, open-if-needed, bill summary, close session.
- Published events: table_session.opened, table_session.closed.
- Consumed events: order.created, payment.recorded, correction.applied.
- Must not leak: client-side authority over totals or closure.

## Open Questions

- Exact approved settlement rules for closing with non-zero balance, if any.
