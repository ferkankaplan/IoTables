# ServiceStaffApp Out of Scope

This document lists behaviors this app must not implement in v1.

## Not Authorized
- It does not create or suspend tenants.
- It does not edit tenant identity or tenant setup data.
- It does not create halls, tables, stations, products, prices, or menu categories.
- It does not create customer orders.
- It does not prepare station items.
- It does not receive payments or close table sessions.
- It does not change item price snapshots.
- It does not rewrite station preparation state except through an explicit correction workflow.

See also: [../_shared/v1-out-of-scope.md](../_shared/v1-out-of-scope.md).
