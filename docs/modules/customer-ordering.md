# Module: Customer Ordering

## Purpose

Customer Ordering owns anonymous customer carts, order submission, orders, order items, idempotency, and order routing to preparation/service workflows.

It converts a validated CustomerOrderingSession cart into billable order records attached to a TableSession.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| CustomerOrderingSession | Session | create, refresh, expire |
| Customer cart | Aggregate | create, update, validate, clear |
| Order | Entity | create and expose |
| OrderItem | Entity | create with price/modifier/note snapshots |
| Order idempotency record | Safety record | create and resolve duplicate submissions |
| Order-to-station routing | Workflow | create station queue records from order items |

## Not Owned

- Menu product definitions and prices.
- TableAccessToken generation.
- TableSession settlement.
- Payment records.
- Station preparation state after queue creation.
- Service delivery state.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| CustomerApp | Manage cart and submit orders | Requires valid session and fresh table presence for submit |
| CashierApp | Read orders and order items | Tenant/session scoped |
| StationStaffApp | Read assigned order items | Authorized stations only |
| ServiceStaffApp | Read ready/delivery items | Authorized halls only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Add/update/remove cart item | Manage anonymous cart | CustomerApp |
| Submit order | Create order transactionally | CustomerApp |
| List my orders | Customer session order visibility | CustomerApp |
| List table orders | TableSession order visibility | CustomerApp, CashierApp |
| Read order item routing | Support station/service views | StationStaffApp, ServiceStaffApp |

## Internal Rules

- CustomerOrderingSession is not created per order.
- One CustomerOrderingSession may create multiple orders.
- Fresh QR verification refreshes existing compatible CustomerOrderingSession when possible.
- Order must link to both CustomerOrderingSession and TableSession.
- Customer cart is not billable until successful order submission.
- Backend recalculates prices and validates availability/modifiers at submission.
- Submitted orders cannot be modified/cancelled by CustomerApp in v1.

## Operational Safety

- Order submission must be idempotent.
- Idempotency key is scoped by at least `tenantId + customerOrderingSessionId + idempotencyKey`.
- TableSession selection/creation, order creation, order items, snapshots, routing records, and idempotency record are one transaction.
- Failed order submission preserves cart.
- Successful order submission clears only the submitted cart.
- Duplicate submit returns original order result.
- No partial order can leak to station/service/cashier views.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| CustomerOrderingSession | Anonymous browser/table session | tenant, table, cookie token, presence window, expiry |
| CustomerCart | In-progress cart | session-owned, non-billable |
| CustomerCartItem | Cart item | product, quantity, modifiers, notes, estimated price |
| Order | Submitted order | links customerOrderingSessionId and tableSessionId |
| OrderItem | Billable order item | price snapshot, modifier snapshot, note, station assignment |
| OrderSubmitIdempotency | Duplicate submit protection | unique scoped key |

## App Surfaces

| App | Usage |
| --- | --- |
| CustomerApp | Primary cart/order surface |
| CashierApp | Reads all TableSession orders |
| StationStaffApp | Reads station-assigned order items |
| ServiceStaffApp | Reads ready/delivery order items |

## Future Service Boundary

- Own data: customer sessions, carts, orders, order items, submit idempotency.
- Own APIs: cart management, order submit, order visibility.
- Published events: order.created, order_item.routed.
- Consumed events: menu item changed, table session closed, tenant suspended.
- Must not leak: trusted pricing authority to frontend.

## Open Questions

- Whether customers can cancel or modify submitted orders after v1.
