# Ordering Context

Ordering owns customer physical presence, anonymous customer ordering sessions, carts, order submission, order records, and order item creation.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [table-presence.md](table-presence.md) | Fresh QR token redemption and presence window |
| [customer-ordering.md](customer-ordering.md) | CustomerOrderingSession, cart, order submission, order visibility |

## Primary Apps

- CustomerApp
- CashierApp read
- StationStaffApp read
- ServiceStaffApp read

## Boundary Rule

Ordering creates billable order records and can call Settlement's public open-session/check command during submission. It does not own TableSession, Check, Payment, or fulfillment state after routing.
