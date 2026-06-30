# Fulfillment Context

Fulfillment owns operational execution after an order item is accepted.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [preparation.md](preparation.md) | Station queues and preparation state |
| [service-delivery.md](service-delivery.md) | Pickup and delivered state after preparation readiness |

## Contract Documents

| Contract | Purpose |
| --- | --- |
| [preparation-contracts.md](preparation-contracts.md) | Preparation queue and station status transition contracts |
| [service-delivery-contracts.md](service-delivery-contracts.md) | Ready item pickup/delivery, same-table bulk delivery, and service queue contracts |

## API Documents

| API Contract | Purpose |
| --- | --- |
| [preparation-api.md](preparation-api.md) | Station queue, preparation transition, and workload endpoints |
| [service-delivery-api.md](service-delivery-api.md) | Ready item, pickup, delivery, bulk delivery, and service workload endpoints |

## Primary Apps

- StationStaffApp
- ServiceStaffApp
- CustomerApp read
- CashierApp read

## Boundary Rule

Fulfillment updates item execution state. It does not cancel billable records, take payments, change menu configuration, or close table sessions.
