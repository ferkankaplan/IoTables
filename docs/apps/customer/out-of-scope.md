# CustomerApp Out of Scope

This document lists behaviors this app must not implement in the current release.

## Current Release Scope
CustomerApp supports only dine-in table QR ordering in the current release.

Out of scope for CustomerApp the current release:

- customer payment or pay-at-table;
- payment provider checkout;
- waiter-entered orders;
- pickup, package service, courier, delivery, phone order, marketplace order, or counter-sale channels;
- customer cancellation or modification of submitted orders;
- fiscal/e-Adisyon/ÖKC document creation.

CustomerApp may show read-only table bill and balance information, but it must not create payment intents, record payments, close sessions, or initiate fiscal receipt flows.

### Modify or Cancel Submitted Orders
Customers cannot directly modify or cancel submitted orders in the first version.

Changes, cancellations, refunds, discounts, or corrections must go through CashierApp or another explicitly authorized staff workflow.

See also: [../_shared/current-release-out-of-scope.md](../_shared/current-release-out-of-scope.md).
