# Module Contracts: Payments

Source module: [payments.md](payments.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `payments.record_payment` | CashierApp | checkId, amountMinor, method, idempotencyKey, API-computed requestHash | Cashier role; Check open; amount positive; amount <= remaining balance; provider payments out of v1 | Reserve payment idempotency row; lock Check; compute remaining; insert Payment; audit | Payment and updated paid amount |
| `payments.void_payment` | CashierApp | paymentId, reason, idempotencyKey, API-computed requestHash | Cashier role; Check open; non-provider v1 payment; reason required | Reserve payment-void idempotency row; lock Check then Payment; set void fields; write cashier correction/audit atomically; duplicate compatible key returns original result | Voided payment and updated paid amount |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `payments.list_payments` | CashierApp | checkId | Cashier role | Payment history for one Check/Adisyon |
| `payments.list_tenant_payments` | CashierApp | businessDay/current day filter, optional method/status/cursor | Cashier role; own tenant only; v1 current business-day window | Cashier-visible tenant payment history |
| `payments.get_paid_amount` | Table Session and Billing | checkId | Internal settlement call | Sum of non-voided payments |
| `payments.get_customer_visible_summary` | CustomerApp | checkId/tableSessionId | Fresh table presence; read-only | Paid and remaining summary as allowed by CustomerApp |
| `payments.get_payment_idempotency_result` | CashierApp/API layer | idempotency key context | Cashier role; same request hash required | Existing payment result or conflict |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `table_session_billing.get_check` | Validate Check/session state. |
| `table_session_billing.record_cashier_correction` | Record payment void correction. |
| `staff_access.require_staff_permission` | Validate cashier permission. |
| `audit.record_event` | Record payment/void events. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `payment.recorded` | Payment is recorded | Bill summary, Audit |
| `payment.voided` | Payment is voided | Bill summary, Audit |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `payment_duplicate` | Same idempotency key/request returns existing payment. |
| `idempotency_conflict` | Same idempotency key used for a different payment or payment-void request. |
| `overpayment_not_allowed` | Amount exceeds current remaining balance. |
| `payment_void_not_allowed` | Payment cannot be voided under v1 rules. |
