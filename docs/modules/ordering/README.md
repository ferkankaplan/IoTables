# Ordering Context

Ordering owns customer physical presence, anonymous customer ordering sessions, carts, order submission, order records, and order item creation.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [table-presence.md](table-presence.md) | Fresh QR token redemption and presence window |
| [customer-ordering.md](customer-ordering.md) | CustomerOrderingSession, cart, order submission, order visibility |

## Contract Documents

| Contract | Purpose |
| --- | --- |
| [table-presence-contracts.md](table-presence-contracts.md) | QR token issuance, redemption, and fresh presence guard contracts |
| [customer-ordering-contracts.md](customer-ordering-contracts.md) | Customer session, cart, order submit, order visibility, and routing contracts |

## API Documents

| API Contract | Purpose |
| --- | --- |
| [table-presence-api.md](table-presence-api.md) | ESP32 QR token, customer QR redemption, and presence state endpoints |
| [customer-ordering-api.md](customer-ordering-api.md) | Cart, order submit, my orders, and table orders endpoints |

## Primary Apps

- CustomerApp
- CashierApp read
- StationStaffApp read
- ServiceStaffApp read

## Boundary Rule

Ordering creates billable order records and can call Settlement's public open-session/check command during submission. It does not own TableSession, Check, Payment, or fulfillment state after routing.
