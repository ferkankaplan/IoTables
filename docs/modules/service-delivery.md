# Module: Service Delivery

## Purpose

Service Delivery owns item pickup and delivery state after station preparation is ready.

It connects station readiness to the customer-visible `Teslim edildi` state.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Delivery status | State | picked_up, delivered |
| Delivery transition | Event | record service staff action |
| Hall-scoped service queue | Read model | ready/delivery items for authorized halls |

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
- `delivered` is the only state mapped to `Teslim edildi` in CustomerApp.
- Service staff can only operate authorized halls.

## Operational Safety

- Delivery transitions must be idempotent.
- Current state must be validated server-side.
- Hall authorization must be checked server-side.
- Concurrent staff actions must not corrupt state.
- Every transition records actor and timestamp.
- Delivered items cannot be modified except explicit recovery.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| DeliveryState | Current service state after readiness | orderItemId, picked_up/delivered status |
| DeliveryTransition | State history | actor, from, to, timestamp |
| ServiceQueue | Read model | PreparationItem.ready plus delivery state for authorized hall/service view |

## App Surfaces

| App | Usage |
| --- | --- |
| ServiceStaffApp | Primary delivery workflow |
| CustomerApp | Shows delivered status |
| CashierApp | Reads service state |

## Future Service Boundary

- Own data: delivery states and transitions.
- Own APIs: list ready items, mark picked up, mark delivered.
- Published events: item.delivered.
- Consumed events: preparation.ready, table_session.closed.
- Must not leak: delivery mutation to CustomerApp.

## Open Questions

- Whether bulk delivery is supported in v1.
- Whether delivery queue is grouped by table, station, age, or order.
