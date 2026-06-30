# Module: Preparation

## Purpose

Preparation owns station queues and station preparation state transitions.

It starts when Customer Ordering routes order items to stations and ends when station work is marked `ready` or the station reports `cannot_prepare`.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Station queue item | Entity | create from order item, read |
| Preparation status | State | pending, preparing, ready, cannot_prepare |
| Preparation exception | State/reason | report impossible item with required reason |
| Station workload | Read model | counts, age, active queue |
| Preparation transition | Event | record who changed state and when |

## Not Owned

- Station definitions, owned by Tenant Setup / Station Setup.
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
| Report cannot prepare | Transition pending/preparing to cannot_prepare with reason | StationStaffApp |
| Read preparation state | Show operational/customer status | CustomerApp, CashierApp, ServiceStaffApp |

## Internal Rules

- Preparation operates on order items, not whole orders.
- One customer order may create work for multiple stations.
- `ready` means station work is finished, not customer delivery.
- Station staff cannot mark items delivered.
- State model in v1:

```text
pending -> preparing -> ready
pending -> cannot_prepare
preparing -> cannot_prepare
```

- `cannot_prepare` is an operational exception, not a cancellation, refund, discount, or price change.
- `cannot_prepare` must include a reason and actor.
- CashierApp handles any customer/account correction through allowed cashier workflows.
- V1 station queue groups items by preparation status and sorts oldest first inside each group.
- One staff user may operate multiple authorized stations; StationStaffApp shows station selection before the queue.
- Station staff can see customer item notes relevant to preparation, but not cashier-only notes or payment data.
- Ready items remain visible until picked up/delivered or until disabled-service-tracking mode treats `ready` as final.
- Minimum v1 station metrics are pending count, preparing count, ready waiting count, oldest pending item age, and average preparation time for the current business day when enough data exists.

## Operational Safety

- Status transitions must be idempotent.
- Current state must be validated server-side.
- Staff assignment must be checked server-side.
- Concurrent updates to the same item must not corrupt state.
- Every transition records actor and timestamp.
- `cannot_prepare` must validate current state and require a reason.
- `cannot_prepare` must be visible to CashierApp.
- Closed-session items cannot be modified except recovery workflows.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| PreparationItem | Station queue item | orderItemId, stationId, status, cannotPrepareReason |
| PreparationTransition | State history | actor, from, to, timestamp |
| StationWorkload | Read model | active counts and ages |

## App Surfaces

| App | Usage |
| --- | --- |
| StationStaffApp | Primary preparation workflow |
| CustomerApp | Shows customer-readable preparation status; `ready` becomes final only when service delivery tracking is disabled |
| CashierApp | Reads prep status |
| ServiceStaffApp | Consumes ready items |

## Future Service Boundary

- Own data: station queue items and preparation transitions.
- Own APIs: list queue, transition status, read prep state.
- Published events: preparation.status_changed, preparation.ready, preparation.cannot_prepare.
- Consumed events: order_item.routed, station.disabled.
- Must not leak: station authorization to frontend-only checks.

## Open Questions

None currently.
