# CashierApp Out of Scope

This document lists behaviors this app must not implement in v1.

## Not Authorized
- It does not create or suspend tenants.
- It does not edit tenant identity or tenant setup data.
- It does not create halls, tables, stations, products, or menu categories.
- It does not prepare station tickets.
- It does not create customer QR access tokens.
- It does not directly mutate station fulfillment state unless a specific correction workflow allows it.
- It does not create customer payment links or pay-at-table flows in v1.
- It does not issue fiscal/e-Adisyon/ÖKC receipts or external fiscal documents in v1.
- It does not split checks, merge checks, move items between checks, or perform item/person-based split payment in v1.

### Single Check / Adisyon
In v1, every active TableSession has exactly one operational Check/Adisyon.

The Check/Adisyon is the cashier-facing bill for the table visit. It groups all submitted orders, order items, price snapshots, payments, and remaining balance for the active TableSession.

V1 does not support:

- multiple checks under the same TableSession;
- split checks;
- merging checks;
- moving items between checks;
- item/person-based payment splitting;
- customer-initiated payment;
- fiscal/e-Adisyon/ÖKC receipt issuance.

Partial payments are still allowed, but they are amount-based payments against the single Check/Adisyon.

### V1 Correction Rules
Allowed CashierApp corrections in v1:

- add an internal cashier note to the active TableSession;
- cancel/void an order item only while its preparation state is `pending` or `cannot_prepare` and before any payment has been recorded for the Check/Adisyon;
- void a payment on an open Check/Adisyon when no external payment provider is involved.

Not allowed in v1:

- manual order items;
- manual discounts;
- service fees;
- refunds after session closure;
- cancellation of items already in `preparing`, `ready`, `picked_up`, or `delivered` state;
- changing item price snapshots directly;
- moving items between checks or sessions.

All v1 correction actions are cashier-authorized, reason-required, idempotent, and audited. Tenant Admin approval is not part of v1 correction flow. Broader override workflows must be introduced explicitly later instead of extending cashier correction silently.

Payment History shows the current business day by default. Historical reporting across arbitrary date ranges is out of v1 unless a reporting workspace is introduced.

More than one cashier may operate the same tenant at the same time. CashierApp must rely on backend transactions, row/version checks, idempotency keys, and actor-specific audit records instead of assuming a single active cashier.

See also: [../_shared/v1-out-of-scope.md](../_shared/v1-out-of-scope.md).
