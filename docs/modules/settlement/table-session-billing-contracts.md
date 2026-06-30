# Module Contracts: Table Session and Billing

Source module: [table-session-billing.md](table-session-billing.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `table_session_billing.open_session_check_if_needed` | Customer Ordering | tenantId, tableId | Tenant/table active; called during accepted order submit | Rely on unique open TableSession; create TableSession and one Check if absent; conflict loads existing open session | Open TableSession and Check |
| `table_session_billing.record_cashier_correction` | CashierApp | checkId, type, targetType, targetId, reason, idempotencyKey, API-computed requestHash | Cashier role; reason required; target eligible by v1 rules | Reserve correction idempotency row; lock Check and target; append correction; mutate allowed target atomically; duplicate compatible key returns original result | Correction result and updated bill summary |
| `table_session_billing.close_session` | CashierApp | tableSessionId/checkId, optional reason | Cashier role; Check open; remaining balance zero; no invalid active state | Lock TableSession and Check; recompute balance; create SessionClosure; close Check/TableSession | Closed session |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `table_session_billing.get_active_table_session` | CustomerApp, CashierApp, Ordering | tenantId/tableId | CustomerApp requires fresh presence for customer-visible reads; Cashier requires role | Active TableSession or none |
| `table_session_billing.get_bill_summary` | CustomerApp, CashierApp | checkId/tableSessionId | CustomerApp fresh presence; Cashier role | Server-calculated total, paid, remaining |
| `table_session_billing.get_check` | CashierApp, Payments | checkId | Cashier/settlement internal scope | Check and session state |
| `table_session_billing.list_cashier_corrections` | CashierApp | checkId | Cashier role | Correction history |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `payments.get_paid_amount` | Compute bill balance. |
| `customer_ordering.list_table_orders` | Compute order item totals. |
| `preparation.read_preparation_state` | Validate item void eligibility. |
| `staff_access.require_staff_permission` | Validate cashier permission. |
| `audit.record_event` | Record corrections and closure. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `table_session.opened` | First accepted order opens session | CashierApp, Audit |
| `check.opened` | V1 Check is created | CashierApp |
| `cashier.correction_applied` | Correction commits | Audit, bill summary readers |
| `table_session.closed` | Session closes | Ordering guards, Payments, Audit |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `active_session_conflict` | Concurrent open found another active session; load existing session. |
| `remaining_balance_not_zero` | Session cannot close until paid in full. |
| `correction_not_allowed` | Target state does not allow requested correction. |
| `check_closed` | Closed Check cannot accept normal payment/correction/closure mutation. |
