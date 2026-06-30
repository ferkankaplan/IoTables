# PlatformApp Out of Scope

This document lists behaviors this app must not implement in v1.

## Not Authorized
PlatformApp must not silently bypass tenant boundaries.

- It does not create customer orders.
- It does not prepare station items.
- It does not close table sessions as a normal cashier flow.
- It does not take payments on behalf of tenant cashiers.
- It does not mutate tenant runtime data unless an explicit support or recovery workflow exists.
- It does not configure fiscal/e-Adisyon/ÖKC integrations in v1.
- It does not configure external payment providers, printer integrations, hardware terminals, or offline POS mode in v1.

### V1 Tenant Scope
PlatformApp creates single-location restaurant tenants in v1.

V1 tenant creation implies these product boundaries:

- one tenant represents one restaurant/location;
- ordering channel is dine-in table QR only;
- DNS is manual outside the application;
- CustomerApp cannot take payments;
- CashierApp records operational payments only;
- no fiscal/e-Adisyon/ÖKC integration;
- no external payment provider integration;
- no waiter-entered order channel;
- no pickup, package service, courier, phone order, marketplace order, or counter-sale channel;
- no offline-first local POS mode.

These limits must be visible to the Platform Owner during tenant creation or tenant review so the created tenant is not misrepresented as a full POS/fiscal system.

See also: [../_shared/v1-out-of-scope.md](../_shared/v1-out-of-scope.md).
