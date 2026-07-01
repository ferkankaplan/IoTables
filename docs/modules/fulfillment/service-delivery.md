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
| List recent deliveries | Show same-day delivered/recent service activity | ServiceStaffApp |
| Mark picked up | Optional intermediate handoff | ServiceStaffApp |
| Mark delivered | Confirm table delivery | ServiceStaffApp |
| Bulk mark delivered | Confirm multiple same-table items in one atomic action | ServiceStaffApp |
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

- Single-item delivery transitions must be duplicate-safe: repeated or stale attempts must return the current server state or fail as stale without corrupting state.
- Bulk delivery transitions must be idempotent as one command.
- Current state must be validated server-side.
- Hall authorization must be checked server-side.
- Concurrent staff actions must not corrupt state.
- Every transition records actor and timestamp.
- Delivered items cannot be modified except explicit recovery.
- Delivery commands must fail closed when service delivery tracking is disabled.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| DeliveryState | none -> picked_up -> delivered, or none -> delivered | tenant, orderItemId, status, updatedBy, updatedAt | Exists only when service delivery tracking is enabled; ready state comes from PreparationItem; delivered items cannot be modified except explicit recovery | Preserve with OrderItem for customer/cashier visibility |
| DeliveryTransition | append-only | deliveryState/orderItem, actor, fromStatus, toStatus, createdAt | Every pickup/delivered transition records actor/time; transitions validate hall scope through Staff Access | Append-only operational history |
| DeliveryBulkIdempotency | processing -> completed / failed | tenant, table, actor, idempotencyKey, requestHash, deliveredOrderItemIds, status | Unique by tenant + actor + idempotencyKey; whole bulk command succeeds or fails as one unit | Retain long enough for service staff/network retries and same-day audit replay |
| ServiceQueue | derived/read-only | ready preparation items, table/hall context, delivery state | Derived from PreparationItem.ready plus DeliveryState; must respect service hall scope | Rebuildable read model |
| ServiceWorkload | derived/read-only | ready count, picked-up count, oldest ready age, delivered count, average ready-to-delivered time | Derived from ready/delivery transitions; metrics are operational only | Rebuildable read model |
| ServiceRecentDelivery | derived/read-only | delivered items, table/hall context, station label, deliveredAt, actor | Same-day recent delivery activity; must respect service hall scope | Rebuildable from DeliveryState/Transition |

## App Surfaces

| App | Usage |
| --- | --- |
| ServiceStaffApp | Primary delivery workflow |
| CustomerApp | Shows delivered status |
| CashierApp | Reads service state |

## Future Service Boundary

- Own data: delivery states, transitions, and bulk delivery idempotency.
- Own APIs: list ready items, list recent deliveries, mark picked up, mark delivered, bulk mark delivered.
- Published events: delivery.status_changed, item.delivered.
- Consumed events: preparation.ready, table_session.closed.
- Must not leak: delivery mutation to CustomerApp.

## Open Questions

None currently.
