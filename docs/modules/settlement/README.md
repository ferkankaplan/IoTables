# Settlement Context

Settlement owns the table visit billing surface: TableSession, Check/Adisyon, payment records, cashier corrections, bill summary, and closure rules.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [table-session-billing.md](table-session-billing.md) | TableSession, single v1 Check/Adisyon, bill summary, closure |
| [payments.md](payments.md) | Cashier-recorded payments and payment voids |

## Primary Apps

- CashierApp
- CustomerApp read-only
- Ordering command use during order submission

## Boundary Rule

Settlement is the financial/runtime authority for payment and closure. CustomerApp cannot mutate Settlement records in v1.
