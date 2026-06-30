# Module: Service Delivery

## Purpose

Service Delivery owns item pickup and delivery state after station preparation is ready when service delivery tracking is enabled for the tenant.

It connects station readiness to the customer-visible `Teslim edildi` state.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Delivery status | State | picked_up, delivered |
| Delivery transition | Event | record service staff action |
| Hall-scoped service queue | Read model | ready/delivery items for authorized halls |
| Service delivery tracking mode | Tenant setting consumer | no runtime authority when disabled |

## Not Owned

- Station preparation before `ready`.
- Service staff hall assignment, owned by Staff Access.
- TableSession billing.
- Payments.
- Customer order creation.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| ServiceStaffApp / Waiter | update delivery state | Authorized halls only |
| ServiceStaffApp / Busser | support delivery where permitted | Authorized halls only |
| CustomerApp | read delivered state | Fresh table presence for table orders |
| CashierApp | read delivery state | Own tenant |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| List ready items | Show service queue | ServiceStaffApp |
| Mark picked up | Optional intermediate handoff | ServiceStaffApp |
| Mark delivered | Confirm table delivery | ServiceStaffApp |
| Read delivery state | Customer/cashier visibility | CustomerApp, CashierApp |

## Internal Rules

- `ready` is produced by Preparation.
- `picked_up` is optional.
- Valid v1 flows: `PreparationItem.ready -> delivered` and `PreparationItem.ready -> picked_up -> delivered`.
- Service Delivery does not store a `ready` DeliveryState row; ready items are derived from PreparationItem.
- When service delivery tracking is enabled, `delivered` is the only Service Delivery state mapped to `Teslim edildi` in CustomerApp.
- Service staff can only operate authorized halls.
- Service Delivery is enabled by default for the initial cafe starter template.
- Tenant Admin may disable service delivery tracking.
- When disabled, ServiceStaffApp routes and delivery mutation commands are unavailable, DeliveryState rows are not created, and `PreparationItem.ready` is the final tracked fulfillment state.
- V1 service queue groups items by table and sorts oldest ready item first inside each table group.
- Service staff may bulk-mark selected items delivered only for the same table.
- Bulk delivery uses one idempotency key, one actor, and server-side validation for every selected item.
- Minimum v1 service metrics are ready count, picked-up count, oldest ready item age, delivered count for the current business day, and average ready-to-delivered time when enough data exists.

## Operational Safety

- Delivery transitions must be idempotent.
- Bulk delivery transitions must be idempotent as one command.
- Current state must be validated server-side.
- Hall authorization must be checked server-side.
- Concurrent staff actions must not corrupt state.
- Every transition records actor and timestamp.
- Delivered items cannot be modified except explicit recovery.
- Delivery commands must fail closed when service delivery tracking is disabled.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| DeliveryState | Current service state after readiness | orderItemId, picked_up/delivered status |
| DeliveryTransition | State history | actor, from, to, timestamp |
| ServiceQueue | Read model | PreparationItem.ready plus delivery state for authorized hall/service view |
| ServiceWorkload | Read model | active counts and age metrics |

## App Surfaces

| App | Usage |
| --- | --- |
| ServiceStaffApp | Primary delivery workflow |
| CustomerApp | Shows delivered status |
| CashierApp | Reads service state |

## Future Service Boundary

- Own data: delivery states and transitions.
- Own APIs: list ready items, mark picked up, mark delivered.
- Published events: delivery.status_changed, item.delivered.
- Consumed events: preparation.ready, table_session.closed.
- Must not leak: delivery mutation to CustomerApp.

## Open Questions

None currently.
