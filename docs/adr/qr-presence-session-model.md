# ADR: QR Presence and Session Model

## Status

Accepted for the current release.

## Context

CustomerApp needs anonymous customers to prove they are physically at a table before submitting orders or reading table-level order and bill state. Each table has an ESP32 display that shows a short-lived, one-time QR token. The ESP32 is a display surface, not a full device-management domain in the current release.

The model separates four concepts:

- TableDisplayCredential authenticates the table display.
- TableAccessToken is the short-lived one-time QR token shown to the customer.
- CustomerOrderingSession is the browser/customer cart and order continuity session.
- TableSession is the billable restaurant table visit.

Sources:

- [../modules/_shared/table-access-qr-flow.md](../modules/_shared/table-access-qr-flow.md)
- [../modules/tenant-setup/table-display-provisioning.md](../modules/tenant-setup/table-display-provisioning.md)
- [../modules/ordering/table-presence.md](../modules/ordering/table-presence.md)
- [../modules/ordering/customer-ordering.md](../modules/ordering/customer-ordering.md)
- [../database/transactions.md](../database/transactions.md)

## Decision

The current release keeps table display provisioning, QR presence, customer ordering continuity, and table billing as separate concepts.

Rules:

- The ESP32 authenticates with a TableDisplayCredential bound to one tenant/table.
- The backend resolves tenant/table from the credential and does not trust table IDs from the ESP32.
- The QR contains a short-lived TableAccessToken, not the display credential.
- QR token redemption is atomic and one-time.
- Successful redemption creates or refreshes fresh presence on a compatible CustomerOrderingSession.
- CustomerOrderingSession is not per order and may submit multiple orders.
- TableSession starts with the first submitted order and represents the billable table visit.
- Fresh presence gates order submission and table orders/bill visibility.
- Presence expiry does not delete the customer cart.

## Consequences

- Table Display Provisioning owns claims and display credentials.
- Table Presence owns QR tokens and fresh presence.
- Customer Ordering owns cart, CustomerOrderingSession, orders, and order idempotency.
- Settlement owns TableSession and Check/Adisyon.
- QR replay protection must be implemented in backend and database, not only in frontend.
- Service recovery for broken/replaced displays uses provisioning/revocation tools without changing TableSession semantics.

## Synchronization Points

- Cross-module QR flow: [../modules/_shared/table-access-qr-flow.md](../modules/_shared/table-access-qr-flow.md)
- Table display module: [../modules/tenant-setup/table-display-provisioning.md](../modules/tenant-setup/table-display-provisioning.md)
- Table presence module: [../modules/ordering/table-presence.md](../modules/ordering/table-presence.md)
- Customer ordering module: [../modules/ordering/customer-ordering.md](../modules/ordering/customer-ordering.md)
- Schema and constraints: [../database/schema.md](../database/schema.md), [../database/indexes-constraints.md](../database/indexes-constraints.md)
- Transaction catalog: [../database/transactions.md](../database/transactions.md)

## Rejected Alternatives

| Alternative | Reason Rejected |
| --- | --- |
| Device equals table as one aggregate | It would mix table setup, credential lifecycle, QR security, and billing semantics. |
| Customer session equals table session | It would lose the difference between browser continuity and the billable table visit. |
| QR token as long-lived table identifier | It would allow replay and remote fake ordering. |
| ESP32-managed session authority | It would move business authority to a weak edge device. |

## Review Trigger

Review this ADR only if current release adds real device inventory, firmware lifecycle, health monitoring, or non-table display devices. Exceptional display replacement does not change this model.
