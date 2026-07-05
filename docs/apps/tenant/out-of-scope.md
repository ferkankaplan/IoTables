# TenantApp Out of Scope

This document lists behaviors this app must not implement in the current release.

## Not Authorized
- It does not create or suspend tenants.
- It does not change immutable tenant identity fields such as tenant name or tenant subdomain.
- It does not manage platform billing, package limits, or global platform settings.
- It does not directly operate customer table sessions as a cashier.
- It does not prepare station tickets as station staff.
- It does not create customer QR ordering sessions.
- It does not configure fiscal/e-Adisyon/ÖKC integrations in the current release.
- It does not configure kitchen printers, receipt printers, cash drawers, payment terminals, or other hardware integrations in the current release.
- It does not configure waiter-entered orders, package service, courier delivery, pickup, phone orders, marketplace orders, counter sales, stock/recipe, cost accounting, or multi-location operations in the current release.

See also: [../_shared/current-release-out-of-scope.md](../_shared/current-release-out-of-scope.md).
