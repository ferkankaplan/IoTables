# Module: Table Session and Billing

## Purpose

Table Session and Billing owns the table-based operational session and the cashier-facing Check/Adisyon.

It groups all accepted orders for a table until CashierApp closes the session. In v1, every TableSession has exactly one Check/Adisyon. The Check calculates totals, paid amount, adjustments, and remaining balance from billable records.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| TableSession | Entity | open, read, close |
| Check / Adisyon | Entity | create one per TableSession, read, close with session |
| Active table session constraint | Invariant | one active session per tenant/table |
| Bill summary | Read model/calculation | total, paid, remaining |
| PriceAdjustment | Entity | correction/future pricing adjustment structure |
| CashierCorrection | Entity | note, item void, payment void with reason |
| CashierCorrectionIdempotency | Safety record | prevent duplicate correction commands |
| Session closure rule | State transition | close only when settlement rules allow |

## Not Owned

- Customer cart.
- QR token redemption.
- Menu pricing definitions.
- Payment method execution.
- Station preparation.
- Service delivery.
- Customer payment/pay-at-table.
- Fiscal/e-Adisyon/ÖKC document issuance.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| CustomerApp | Read active TableSession orders and bill summary | Requires fresh table presence; read-only |
| CashierApp | Read session, receive payment through Payments, close session | Cashier permission required |
| Customer Ordering | Open/select active TableSession and Check during order submission | Transactional command only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Get active table session | Attach/read current table session | CustomerApp, CashierApp, Customer Ordering |
| Open session/check if needed | First accepted order creates session and single Check | Customer Ordering |
| Get bill summary | Show totals and balance | CustomerApp, CashierApp |
| Record cashier correction | Apply narrow current release correction with reason | CashierApp |
| Close session | End table session after settlement | CashierApp |

## Internal Rules

- TableSession is table-based, not customer-based.
- One active TableSession may exist per tenant/table.
- First accepted order opens a TableSession and one Check when none exists.
- The current release has exactly one Check per TableSession.
- Split checks, merged checks, moving items between checks, and item/person-based payment splitting are out of the current release.
- Closed TableSession cannot accept new orders or payments except explicit recovery.
- CustomerApp can read bill summary but cannot settle, discount, or close.
- CashierApp performs settlement and closure.
- Menu prices are VAT/tax-inclusive operational prices in the current release.
- Separate tax calculation, manual discounts, service fees, campaigns, customer price confirmation, customer payments, and fiscal receipt issuance are out of the current release.
- PriceAdjustment exists for explicit correction/future pricing structure; it must not become broad discount power.
- Current release cashier corrections are limited to note-only correction, item void while preparation is `pending` or `cannot_prepare` before any Check payment, and non-provider payment void on an open Check.

## Operational Safety

- Active TableSession creation must be concurrency-safe.
- Database must enforce one active session per tenant/table.
- Database must enforce one Check per TableSession in the current release.
- Session closure must be idempotent.
- Bill summary must be calculated server-side from order item price snapshots, corrections, and payment records.
- Session must not close with remaining balance in the current release.
- Correction commands must reserve idempotency, validate target state server-side, and write audit events in the same transaction.
- Check and TableSession closure must be one transaction.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| TableSession | open -> closed | tenant, table, status, openedAt, closedAt | Only one active TableSession per tenant/table; closed sessions cannot accept normal orders/payments | Preserve permanently as visit history |
| Check / Adisyon | open -> closed | tenant, tableSession, status, openedAt, closedAt | Exactly one Check per TableSession in the current release; total is server-calculated from OrderItem snapshots, corrections/voids, adjustments, and payments | Preserve permanently as bill history |
| PriceAdjustment | created | tenant, check, optional orderItem, type, amount, reason, createdBy, createdAt | The current release does not expose manual discounts/service fees/tax/campaigns; exists to keep future adjustment structure explicit | Append-only unless an explicit reversal model is introduced |
| CashierCorrection | created | tenant, check, type, targetType, targetId, reason, cashier, createdAt | Reason required; current release allows note, eligible item void, and eligible non-provider payment void only | Append-only; never rewrite correction history |
| CashierCorrectionIdempotency | processing -> completed / failed | tenant, check, idempotencyKey, requestHash, cashierCorrectionId, status, completedAt | Unique by tenant + check + idempotencyKey; same key/request returns original correction result | Retain with operational audit window for correction replay and investigation |
| BillSummary | calculated/read model | check, total, paid, remaining | Server-calculated only; CustomerApp can read with fresh presence but cannot mutate | Rebuildable from billable records |
| SessionClosure | created at close | tableSession, check, cashier, closedAt, reason when needed | Close requires zero remaining balance in the current release and current-state validation | Preserve as part of session/check history |

## App Surfaces

| App | Usage |
| --- | --- |
| CustomerApp | Reads table orders and bill summary with fresh presence |
| CashierApp | Primary settlement and session closure surface |

## Future Service Boundary

- Own data: table sessions, checks, correction records, correction idempotency, price adjustments, billing read models.
- Own APIs: active session lookup, open session/check if needed, bill summary, correction command, close session.
- Published events: table_session.opened, check.opened, cashier.correction_applied, table_session.closed.
- Consumed events: order.created, payment.recorded, payment.voided.
- Must not leak: client-side authority over totals or closure.

## Open Questions

None currently.
