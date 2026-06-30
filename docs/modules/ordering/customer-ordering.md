# Module: Customer Ordering

## Purpose

Customer Ordering owns anonymous customer sessions, carts, order submission, orders, order items, idempotency, and order routing to preparation/service workflows.

It converts a validated CustomerOrderingSession cart into billable order records attached to Settlement's active TableSession and single v1 Check/Adisyon.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| CustomerOrderingSession | Session | create, refresh, expire |
| Customer cart | Aggregate | create, update, validate, clear |
| Order | Entity | create and expose |
| OrderItem | Entity | create with product variant, price/modifier/note snapshots |
| Order idempotency record | Safety record | create and resolve duplicate submissions |
| Order-to-station routing | Workflow | create station queue records from order items |
| Order channel | Value | `dine_in_qr` only in v1 |

## Not Owned

- Menu product definitions, variants, availability, and prices.
- TableAccessToken generation.
- TableSession settlement.
- TableSession and Check ownership.
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
- Backend recalculates prices and validates selected variant, availability, and modifiers at submission.
- V1 does not have a separate order price preview/quote endpoint or customer price-confirmation step.
- Frontend totals are informational only; final price snapshots are created server-side during submission.
- V1 creates only `dine_in_qr` orders.
- Waiter-entered, pickup, delivery, package, phone, marketplace, and counter-sale channels are out of v1.
- Submitted orders cannot be modified/cancelled by CustomerApp in v1.
- Customer Ordering calls Settlement's public open-session/check command during submission. It does not own TableSession or Check.

## Operational Safety

- Order submission must be idempotent.
- Idempotency key is scoped by at least `tenantId + customerOrderingSessionId + idempotencyKey`.
- Settlement session/check selection or creation, order creation, order items, snapshots, routing records, and idempotency record are one transaction.
- Failed order submission preserves cart.
- Successful order submission clears only the submitted cart.
- Duplicate submit returns original order result.
- No partial order can leak to station/service/cashier views.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| CustomerOrderingSession | active -> expired | tenant, table, tableSessionId nullable, cookieTokenHash, presenceValidUntil, expiresAt, lastSeenAt | Not customer identity; not per order; may submit multiple orders; fresh QR refreshes compatible session | Expire by retention policy; losing it may lose My Orders continuity but not TableSession records |
| CustomerCart | active -> submitted / abandoned | tenant, customerOrderingSessionId, status, timestamps | One active cart per CustomerOrderingSession in v1; cart is non-billable until submit; failed submit preserves cart | Submitted cart closes/clears only after order transaction commits; abandoned carts can expire |
| CustomerCartItem | active with cart -> submitted/removed | cart, clientCartItemId, productServiceId, productVariantId, quantity, selectedModifiers, note, estimatedPrice | Client price is not trusted; product/variant/modifier/availability revalidated server-side | Removed/submitted cart items need not become billable history; OrderItem is the durable record |
| Order | submitted | tenant, id, customerOrderingSessionId, tableSessionId, submittedAt, orderChannel | V1 creates only `dine_in_qr`; order links both My Orders owner and table billing session | Preserve; CustomerApp cannot cancel or mutate submitted orders |
| OrderItem | submitted -> optionally cashier-voided | tenant, order, product/variant IDs, stationId snapshot, name/variant/price/modifier snapshots, quantity, note, void fields | Snapshots created server-side; direct snapshot edits forbidden; station routing snapshot does not change after catalog routing updates | Preserve even when voided; void is explicit correction metadata |
| OrderSubmitIdempotency | processing -> completed / failed | tenant, customerOrderingSessionId, idempotencyKey, requestHash, orderId, status | Unique by tenant + customerOrderingSessionId + idempotencyKey; same key/different request fails closed | Retain long enough to cover client/network retries and audit duplicate-submit protection |

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

None currently.
