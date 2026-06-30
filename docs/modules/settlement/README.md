# Settlement Context

Settlement owns the table visit billing surface: TableSession, Check/Adisyon, payment records, cashier corrections, bill summary, and closure rules.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [table-session-billing.md](table-session-billing.md) | TableSession, single v1 Check/Adisyon, bill summary, closure |
| [payments.md](payments.md) | Cashier-recorded payments, payment history, and payment voids |

## Contract Documents

| Contract | Purpose |
| --- | --- |
| [table-session-billing-contracts.md](table-session-billing-contracts.md) | TableSession, Check, bill summary, correction, and close-session contracts |
| [payments-contracts.md](payments-contracts.md) | Payment record, payment history, payment void, idempotency, and payment summary contracts |

## API Documents

| API Contract | Purpose |
| --- | --- |
| [table-session-billing-api.md](table-session-billing-api.md) | Active table session, check, bill summary, correction, and close-session endpoints |
| [payments-api.md](payments-api.md) | Check payment list, tenant payment history, record, void, and customer payment summary endpoints |

## Primary Apps

- CashierApp
- CustomerApp read-only
- Ordering command use during order submission

## Boundary Rule

Settlement is the financial/runtime authority for payment and closure. CustomerApp cannot mutate Settlement records in v1.
