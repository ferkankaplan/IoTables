# TenantApp Out of Scope

This document lists behaviors this app must not implement in v1.

## Not Authorized
- It does not create or suspend tenants.
- It does not change immutable tenant identity fields such as tenant name or tenant subdomain.
- It does not manage platform billing, package limits, or global platform settings.
- It does not directly operate customer table sessions as a cashier.
- It does not prepare station tickets as station staff.
- It does not create customer QR ordering sessions.
- It does not configure fiscal/e-Adisyon/ÖKC integrations in v1.
- It does not configure kitchen printers, receipt printers, cash drawers, payment terminals, or other hardware integrations in v1.
- It does not configure waiter-entered orders, package service, courier delivery, pickup, phone orders, marketplace orders, counter sales, stock/recipe, cost accounting, or multi-location operations in v1.

See also: [../_shared/v1-out-of-scope.md](../_shared/v1-out-of-scope.md).
