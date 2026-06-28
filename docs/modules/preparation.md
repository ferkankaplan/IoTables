# Module: Preparation

## Purpose

Preparation owns station queues and station preparation state transitions.

It starts when Customer Ordering routes order items to stations and ends when station work is marked `ready`.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Station queue item | Entity | create from order item, read |
| Preparation status | State | pending, preparing, ready |
| Station workload | Read model | counts, age, active queue |
| Preparation transition | Event | record who changed state and when |

## Not Owned

- Station definitions, owned by TenantApp/Station Management data.
- Product-to-station assignment, owned by Menu Catalog.
- Customer delivery state after `ready`.
- Payments and table billing.
- Order creation transaction before queue item exists.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| StationStaffApp / Station Staff | read and update assigned station items | Authorized stations only |
| CashierApp | read preparation state | Own tenant |
| CustomerApp | read customer-readable state | Read-only |
| ServiceStaffApp | consume ready items | Authorized halls/service scope |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Create queue item | Add order item to station queue | Customer Ordering |
| List station queue | Show staff queue | StationStaffApp |
| Start preparing | Transition pending to preparing | StationStaffApp |
| Mark ready | Transition preparing to ready | StationStaffApp |
| Read preparation state | Show operational/customer status | CustomerApp, CashierApp, ServiceStaffApp |

## Internal Rules

- Preparation operates on order items, not whole orders.
- One customer order may create work for multiple stations.
- `ready` means station work is finished, not customer delivery.
- Station staff cannot mark items delivered.
- State model in v1: `pending -> preparing -> ready`.

## Operational Safety

- Status transitions must be idempotent.
- Current state must be validated server-side.
- Staff assignment must be checked server-side.
- Concurrent updates to the same item must not corrupt state.
- Every transition records actor and timestamp.
- Closed-session items cannot be modified except recovery workflows.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| PreparationItem | Station queue item | orderItemId, stationId, status |
| PreparationTransition | State history | actor, from, to, timestamp |
| StationWorkload | Read model | active counts and ages |

## App Surfaces

| App | Usage |
| --- | --- |
| StationStaffApp | Primary preparation workflow |
| CustomerApp | Shows `Hazırlanıyor` until delivery |
| CashierApp | Reads prep status |
| ServiceStaffApp | Consumes ready items |

## Future Service Boundary

- Own data: station queue items and preparation transitions.
- Own APIs: list queue, transition status, read prep state.
- Published events: preparation.ready.
- Consumed events: order_item.routed, station.disabled.
- Must not leak: station authorization to frontend-only checks.

## Open Questions

- Queue grouping strategy: table, station, age, order, product.
- Whether station staff can report/reject impossible items.
