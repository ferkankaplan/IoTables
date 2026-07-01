# Module Contracts: Service Delivery

Source module: [service-delivery.md](service-delivery.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `service_delivery.mark_picked_up` | ServiceStaffApp | orderItemId or preparationItemId | Service delivery tracking enabled; PreparationItem is `ready`; actor has hall scope | Create/lock DeliveryState; transition to `picked_up`; append transition | Picked-up delivery state |
| `service_delivery.mark_delivered` | ServiceStaffApp | orderItemId or preparationItemId | Service delivery tracking enabled; item is ready or picked_up; actor has hall scope | Create/lock DeliveryState; direct ready-to-delivered is allowed; append transition | Delivered delivery state |
| `service_delivery.bulk_mark_delivered` | ServiceStaffApp | tableId, orderItemIds, idempotencyKey, API-computed requestHash | Service tracking enabled; all items same table; actor has hall scope; every item is ready or picked_up; no partial success | Reserve bulk idempotency row; lock all target items/states in deterministic order; validate all; transition all to delivered; append transitions atomically | Bulk delivery result |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `service_delivery.list_ready_items` | ServiceStaffApp | actor, hall filters | Service staff role and hall assignment; tracking enabled | Ready/picked-up service queue |
| `service_delivery.list_recent_deliveries` | ServiceStaffApp | actor, hall filters, current business day, cursor/limit | Service staff role and hall assignment; tracking enabled | Same-day delivered/recent service activity |
| `service_delivery.read_delivery_state` | CustomerApp, CashierApp | orderItemId/session filter | App visibility rules; CustomerApp sees mapped text only | Delivery state or derived final state |
| `service_delivery.get_service_workload` | ServiceStaffApp | actor/hall filters | Hall assignment | Ready/picked-up/delivered counters |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `preparation.read_preparation_state` | Confirm item is ready. |
| `staff_access.require_staff_permission` | Validate service staff and hall scope. |
| `venue_layout.get_table_context` | Resolve hall/table for scope and display. |
| `audit.record_event` | Record delivery transitions. |

## Settings Dependency

Service Delivery reads `TenantOperationalSettings.serviceDeliveryTrackingEnabled` but does not own it. When tracking is disabled, this module does not mutate old delivery history; customer/cashier visibility maps `PreparationItem.ready` as the final fulfillment signal.

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `delivery.status_changed` | Pickup or delivered transition commits | Customer/Cashier visibility, Audit |
| `delivery.bulk_delivered` | Bulk delivery command commits | Customer/Cashier visibility, Audit |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `service_tracking_disabled` | Tenant does not use ServiceStaffApp delivery tracking. |
| `not_ready_for_delivery` | PreparationItem is not ready. |
| `outside_hall_scope` | Actor cannot operate the table/hall for this item. |
| `invalid_delivery_transition` | DeliveryState cannot move to requested state. |
| `bulk_mixed_table` | Selected items are not all on the requested table. |
| `bulk_item_invalid` | At least one selected item fails readiness, scope, or state validation. |
| `idempotency_conflict` | Same idempotency key was used for a different bulk request. |
