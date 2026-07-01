# CashierApp Analytics

CashierApp analytics defines cashier-visible settlement measurements for current operational work. It does not replace payment records, Check/Adisyon calculation, audit evidence, or accounting/reporting products.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [out-of-scope.md](out-of-scope.md)
- [../../modules/settlement/table-session-billing.md](../../modules/settlement/table-session-billing.md)
- [../../modules/settlement/payments.md](../../modules/settlement/payments.md)
- [../../modules/governance/audit.md](../../modules/governance/audit.md)

## Analytics vs Audit

| Concern | CashierApp Analytics | Audit |
| --- | --- | --- |
| Purpose | Summarize active balances, current-day payments, voids, and closure workload. | Preserve immutable evidence for payments, voids, corrections, and closures. |
| Mutability | Derived/rebuildable from settlement records. | Append-only. |
| Authority | Never calculates final bill authority or authorizes payment/close/correction. | Evidence only. |
| Detail | Counts, sums, current business-day operational metrics. | Actor, action, target, reason, timestamp, safe metadata. |

BillSummary and Payment records remain the financial source of truth. Analytics must not become a ledger.

## V1 Metrics

| Metric | Source | Notes |
| --- | --- | --- |
| Active table session count | Table Session and Billing | Current open sessions only. |
| Open remaining balance total | BillSummary | Operational total, server-calculated. |
| Payment count today | Payments | Current business day. |
| Payment amount today by method | Payments | `cash`, `card`, `transfer`. |
| Voided payment count today | Payments + CashierCorrection | Current business day. |
| Correction count today | Table Session and Billing | Note/item void/payment void counts. |
| Closed session count today | Table Session and Billing | Explicit cashier closures. |
| Cannot-prepare attention count | Preparation read via session/order detail | Operational attention only. |

## Allowed Surfaces

| Surface | Analytics Behavior |
| --- | --- |
| Cashier Workspace | Active sessions, open balance summary, attention counts. |
| Session Detail | Server-calculated totals and correction/payment indicators. |
| Payment History | Current business-day payment totals and filters. |

Cashier analytics should stay inside existing settlement surfaces. A broad reporting workspace is out of v1.

## Data Boundaries

CashierApp analytics may use:

- active TableSession and Check state;
- server-calculated BillSummary;
- Payment records and void state;
- CashierCorrection records;
- cashier-visible preparation/delivery attention flags;
- cashier-visible audit aggregates for settlement evidence.

CashierApp analytics must not show:

- customer identity or cart internals;
- platform tenant internals;
- tenant setup mutation controls;
- station/service mutation controls;
- external provider settlement data;
- tax/fiscal/e-Adisyon/ÖKC reporting outputs;
- arbitrary historical accounting reports.

## Refresh and Consistency

- Analytics cards can be eventually consistent.
- Payment, void, correction, and close commands must re-read authoritative server state.
- If analytics and BillSummary disagree, BillSummary wins.
- If analytics and Payment records disagree, Payment records win.
- Analytics failure must not block payment/correction/close flows when authoritative reads are healthy.

## V1 Out of Scope

- Full accounting reports.
- Fiscal/e-Adisyon/ÖKC documents.
- Arbitrary historical reports.
- Split-check or item/person settlement analytics.
- Refund analytics after session closure.
- External provider reconciliation.
- Staff ranking/productivity reports.

## Acceptance

CashierApp analytics is acceptable when:

- it summarizes current operational settlement state without becoming a ledger;
- it stays inside existing cashier surfaces;
- all money values trace to Settlement/Payments source records;
- analytics never authorizes payment, correction, void, or close;
- audit remains immutable evidence for sensitive settlement actions.
