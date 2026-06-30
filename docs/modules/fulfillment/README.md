# Fulfillment Context

Fulfillment owns operational execution after an order item is accepted.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [preparation.md](preparation.md) | Station queues and preparation state |
| [service-delivery.md](service-delivery.md) | Pickup and delivered state after preparation readiness |

## Primary Apps

- StationStaffApp
- ServiceStaffApp
- CustomerApp read
- CashierApp read

## Boundary Rule

Fulfillment updates item execution state. It does not cancel billable records, take payments, change menu configuration, or close table sessions.
