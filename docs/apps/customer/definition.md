# CustomerApp

## Purpose

CustomerApp is the anonymous customer ordering interface opened from the QR displayed on the table screen.

It is the core customer experience of IoTables. It lets a customer prove fresh table presence, browse the tenant menu, build a cart, and submit orders to the correct table session.

CustomerApp is not an admin, cashier, or station staff interface. It must optimize for customer experience while protecting the tenant from fake, stale, duplicated, or cross-table orders.

## Current Release Scope

CustomerApp supports only dine-in table QR ordering in the current release.

Out of scope for CustomerApp the current release:

- customer payment or pay-at-table;
- payment provider checkout;
- waiter-entered orders;
- pickup, package service, courier, delivery, phone order, marketplace order, or counter-sale channels;
- customer cancellation or modification of submitted orders;
- fiscal/e-Adisyon/ÖKC document creation.

CustomerApp may show read-only table bill and balance information, but it must not create payment intents, record payments, close sessions, or initiate fiscal receipt flows.

## Locked Session Model

CustomerApp uses three separate concepts. These must not be merged.

```text
TableAccessToken
  short-lived, one-time QR token shown on the table screen

CustomerOrderingSession
  anonymous browser session created after a valid QR redeem

TableSession
  table-based operational/billing session opened by the first order and closed by cashier
```

Initial current release timing policy:

| Concept | Lifetime |
| --- | --- |
| TableAccessToken | 60 seconds |
| Fresh table presence | 2 minutes |
| CustomerOrderingSession | 30 minutes |

### TableAccessToken

TableAccessToken proves that someone scanned the current QR shown on a physical table screen.

Rules:

- It is generated server-side.
- It is shown by the ESP32 table screen.
- It is short-lived.
- It is one-time use.
- It is consumed atomically.
- It must not contain plain table IDs or trusted client-side authority.
- It must be stored server-side in a way that supports replay prevention.

V1 lifetime:

```text
60 seconds
```

### CustomerOrderingSession

CustomerOrderingSession represents an anonymous browser that recently redeemed a valid table QR.

It is not a customer identity. The system does not know who the customer is. The only trusted fact is:

```text
This browser recently redeemed a fresh QR for this table.
```

Rules:

- It is tenant-scoped.
- It is table-scoped.
- It is browser-scoped.
- It owns the customer's in-progress cart.
- It may reference the currently active TableSession for its table.
- It may contain multiple submitted orders.
- It may allow menu browsing.
- It does not by itself allow order submission.
- It stores the latest fresh table presence window.
- It should be represented to the browser with an opaque secure cookie.

Cookie requirements:

- `HttpOnly`
- `Secure`
- appropriate `SameSite` policy
- short-lived
- opaque random value
- server-side session lookup

V1 lifetime:

```text
30 minutes
```

A CustomerOrderingSession is not created per order. It represents the browser's anonymous visit to the table. The same CustomerOrderingSession may submit multiple orders while it remains valid.

Fresh QR verification should refresh the existing CustomerOrderingSession when possible. It should not create a new CustomerOrderingSession per order.

### Fresh Table Presence

Fresh table presence is required before order submission.

Redeeming a valid TableAccessToken updates the CustomerOrderingSession presence window:

```text
presenceValidUntil = redeemedAt + 2 minutes
```

Menu browsing can continue while CustomerOrderingSession is valid. Order submission must fail or require fresh QR verification when `presenceValidUntil` has expired.

If the browser already has a valid CustomerOrderingSession for the same tenant and table, redeeming a fresh TableAccessToken updates that existing session. A new CustomerOrderingSession is created only when no valid compatible session exists.

This balances security and UX:

- Customers can browse without repeatedly scanning QR.
- Orders still require recent physical presence at the table.
- A QR photo or stale browser session cannot keep submitting orders indefinitely.

### TableSession

TableSession is the table-based operational and billing session.

It is not user-based. It belongs to the tenant and table.

Rules:

- It is opened by the first accepted order for a table when no active TableSession exists.
- It groups all orders for that table until cashier closes it.
- Multiple CustomerOrderingSessions may submit orders into the same TableSession.
- It is closed by CashierApp after settlement.
- A closed TableSession must not accept new orders.

### Customer Session to Table Session Binding

CustomerOrderingSession and TableSession must remain separate.

The cart belongs to CustomerOrderingSession, not TableSession. This protects the customer UX: the cart can survive menu browsing, fresh QR re-verification, and order submission failures without mutating the table bill.

When a CustomerOrderingSession is created or refreshed:

- if the table has an active TableSession, the CustomerOrderingSession joins that TableSession context;
- if the table has no active TableSession, the CustomerOrderingSession remains table-scoped without a TableSession;
- when the first accepted order is submitted, a new TableSession is created and the CustomerOrderingSession joins it.

Joining a TableSession does not move the cart into the TableSession. Only a successfully submitted order creates billable records inside TableSession.

Order submission must re-check the active TableSession server-side. A stale `tableSessionId` from the browser or an old CustomerOrderingSession must never be trusted.

If the joined TableSession was closed before the customer submits the cart, CustomerApp must not attach the order to the closed session. It should require fresh table presence and then either attach to the current active TableSession or create a new TableSession if the table is allowed to accept a new order.

## Menu Experience

CustomerApp must provide a polished mobile-first menu experience. The menu is the main customer-facing product surface.

The customer should be able to browse quickly, understand what is available, customize items, add notes, and build a cart without losing table context.

### Menu Structure

The menu should support:

- categories,
- product/service cards,
- product/service detail panels,
- product images,
- product descriptions,
- prices,
- variants/portions,
- availability state,
- modifiers/options,
- per-item customer notes,
- add-to-cart controls.

Categories should be easy to scan and switch. Product cards should show the minimum needed information: image, name, short description when available, price, availability, and add action.

Product images are supported but not mandatory for every product. Products without images should use a polished fallback state instead of breaking the menu layout.

### Product Detail

Selecting a product opens a contextual detail panel or bottom sheet instead of navigating away from the menu.

Product detail should support:

- larger image,
- full description,
- variant/portion selection when the product has more than one orderable variant,
- quantity,
- required modifiers,
- optional modifiers,
- per-item note,
- final visible item estimate,
- add to cart.

CustomerApp may show an estimated price, but the backend is the pricing authority. Final order pricing is calculated server-side at submission time.

The current release does not have a separate price preview or customer price-confirmation step. Menu prices are expected to be stable during normal customer ordering. If the cart is no longer valid at submission time because a product, variant, modifier, availability, or tenant/table state changed, CustomerApp rejects the affected submission and keeps the cart editable instead of asking the customer to approve a new price.

### Modifiers and Options

Products/services may have variants/portions and modifiers/options.

Variants/portions define the orderable unit and current price, such as small/large coffee or single/double portion. A simple single-price product still uses one default variant behind the scenes.

Examples:

- coffee size,
- portion size,
- milk type,
- extra shot,
- sugar preference,
- cooking preference,
- add-ons,
- remove ingredients,
- service-specific choices.

Modifier rules must support at least:

- required single choice,
- optional single choice,
- optional multiple choice,
- quantity-based add-ons,
- price-changing modifiers,
- zero-price preferences.

The UI must clearly show required variant and modifier choices before allowing add-to-cart. Invalid product configurations must not enter the cart.

### Availability

CustomerApp must respect product and variant availability.

Unavailable products or variants should remain visible only if that helps the tenant UX, but they must not be orderable. Availability must be checked again server-side during order submission.

## Cart Experience

The cart belongs to the anonymous CustomerOrderingSession and current table context.

The cart should survive normal menu browsing, panel navigation, and fresh QR re-verification. If fresh table presence expires, the cart must be preserved while CustomerApp asks the customer to scan the current table QR again.

The cart survives fresh QR verification because the existing CustomerOrderingSession is refreshed instead of replaced.

The cart should persist across browser refresh while the CustomerOrderingSession cookie remains valid. If the cookie is deleted or the CustomerOrderingSession expires, the cart may be lost.

### Cart Item

Each cart item should include:

- product/service id,
- product variant id,
- quantity,
- selected modifiers/options,
- per-item customer note,
- client-visible estimated price,
- idempotency-safe client cart item id.

The cart must not be treated as trusted order data. The backend must revalidate all products, variants, modifiers, availability, prices, and tenant/table context at order submission.

### Cart Controls

CustomerApp should support:

- increase/decrease quantity,
- remove item,
- edit modifiers/options,
- edit item note,
- show estimated subtotal,
- preserve cart during fresh QR verification,
- clear cart after successful order submission.

### Cart Validation

Before order submission, CustomerApp should show frontend validation errors for a better UX. Backend validation is still mandatory.

Validation examples:

- unavailable product,
- missing required modifier,
- invalid modifier combination,
- invalid quantity,
- stale menu data,
- expired fresh table presence.

## Order Submission Gate

CustomerApp must pass all checks before creating an order:

1. CustomerOrderingSession exists and is valid.
2. CustomerOrderingSession tenant and table match the requested order context.
3. Fresh table presence is still valid.
4. Cart is valid and priced server-side.
5. Table can accept orders.
6. Active TableSession is open or a new TableSession can be opened atomically.
7. CustomerOrderingSession is joined to the correct current TableSession.
8. Idempotency key has not already created a different order.

If fresh table presence is expired, CustomerApp should preserve the cart and ask the customer to scan the current table QR again.

## Fresh QR Verification UX

Fresh QR verification should feel like a lightweight table confirmation, not an error state.

When fresh table presence is missing or expired:

1. CustomerApp preserves the cart.
2. CustomerApp explains that order submission requires current table verification.
3. Customer scans the current QR shown on the table screen.
4. CustomerApp redeems the token.
5. Existing CustomerOrderingSession is refreshed when possible.
6. Customer returns to the preserved cart and can submit again.

Customer-facing messages should be direct and calm.

| Case | UX Behavior |
| --- | --- |
| Fresh presence expired | Ask customer to scan the current table QR again and preserve cart |
| QR token expired | Ask customer to scan the newly displayed QR |
| QR token already used | Ask customer to scan the newly displayed QR |
| QR belongs to another table | Reject and ask customer to scan the QR on their own table |
| Customer session expired | Create or refresh session after valid QR scan; cart may be lost if no recoverable session exists |

CustomerApp must not expose token internals or security terminology to customers.

## Order Creation Flow

Order creation converts the CustomerOrderingSession cart into billable table-session records.

The whole operation must be backend-owned, idempotent, and transactionally consistent.

### Submit Order

1. Customer presses `Order`.
2. Frontend sends the current cart with an idempotency key.
3. Backend validates CustomerOrderingSession.
4. Backend validates fresh table presence.
5. Backend validates tenant, table, products, variants, modifiers, availability, and quantities.
6. Backend calculates final prices server-side.
7. Backend checks or creates the current active TableSession atomically.
8. Backend joins CustomerOrderingSession to the current TableSession.
9. Backend creates Order with both `customerOrderingSessionId` and `tableSessionId`.
10. Backend creates OrderItems with product, variant, price, modifier, note, and station snapshots.
11. Backend creates station queue records for the OrderItems.
12. Backend commits the transaction.
13. CustomerApp clears the submitted cart and shows the order confirmation.

### Required Order Links

Each order must retain both relationships:

| Relationship | Purpose |
| --- | --- |
| `order.customerOrderingSessionId` | Powers My Orders for the anonymous browser session |
| `order.tableSessionId` | Powers Table Orders, CashierApp, billing, and settlement |

### Transaction Boundary

These records must be created in one transaction:

- TableSession creation or selection,
- CustomerOrderingSession to TableSession join,
- Order,
- OrderItems,
- product/variant snapshots,
- price snapshots,
- modifier snapshots,
- station queue records,
- idempotency record.

If any part fails, no partial order should become visible to stations, cashier, or customer history.

### Idempotency

Order submit requires an idempotency key.

The key must be scoped at least by:

```text
tenantId + customerOrderingSessionId + idempotencyKey
```

If the same key is submitted again:

- return the original successful order when it exists;
- do not create a second order;
- return the same validation/rejection result when the original attempt failed in a durable way.

Frontend duplicate-submit prevention is still required, but backend idempotency is the authority.

## Post-Order Visibility

CustomerApp should show a clear post-order confirmation and support two order views.

### Order Confirmation

After successful submission, CustomerApp should show:

- order accepted message,
- submitted order summary,
- item quantities,
- selected modifiers,
- item notes,
- customer-readable item status,
- actions to view orders or return to menu.

The submitted cart is cleared only after successful order creation. If order creation fails, the cart remains available for correction or retry.

### My Orders

My Orders shows orders submitted by the current CustomerOrderingSession.

Rules:

- A CustomerOrderingSession may submit multiple orders.
- All orders submitted by the same valid CustomerOrderingSession appear in My Orders.
- If the customer orders tea, receives it, and orders another tea later from the same browser/session, My Orders shows both orders.
- Fresh QR verification refreshes the same CustomerOrderingSession when possible, so previous My Orders remain visible.
- If the cookie is deleted or the CustomerOrderingSession expires, My Orders may no longer show earlier orders from the old session.

### Table Orders

Table Orders shows all orders attached to the active TableSession for the table.

Rules:

- Table Orders can recover visibility when the browser cookie is lost, because TableSession is stored server-side.
- Table Orders requires fresh table presence.
- Table Orders must be read-only for customers.
- CustomerApp may show order items and customer-readable preparation status.
- Table Orders should include order time, item time/status, quantities, selected modifiers, item notes, item prices, and order totals.
- CustomerApp may show table bill and balance summary, but customers cannot settle or mutate payments from CustomerApp.

### Table Bill and Balance

CustomerApp should show a read-only bill summary for the active TableSession.

The bill summary requires fresh table presence and must be calculated server-side.

It should include:

- table total,
- paid amount,
- remaining balance,
- order totals,
- order times,
- item-level prices,
- item-level customer-readable status,
- payment/balance state.

CustomerApp must not allow customers to mark payments, close sessions, apply discounts, cancel items, or edit billable records. Those actions belong to CashierApp or another explicitly authorized staff workflow.

### Customer-Readable Status

Internal preparation and delivery states should be mapped to simple customer language.

When service delivery tracking is enabled:

| Internal State | Customer Text |
| --- | --- |
| `PreparationItem.pending` | `Hazırlanıyor` |
| `PreparationItem.preparing` | `Hazırlanıyor` |
| `PreparationItem.ready` | `Hazırlanıyor` |
| `DeliveryState.picked_up` | `Hazırlanıyor` |
| `DeliveryState.delivered` | `Teslim edildi` |

`PreparationItem.ready` means station work is finished, not that the customer received the item. For table service, CustomerApp should show `Hazırlanıyor` until ServiceStaffApp marks the item as `DeliveryState.delivered`.

When service delivery tracking is disabled for the tenant:

| Internal State | Customer Text |
| --- | --- |
| `PreparationItem.pending` | `Hazırlanıyor` |
| `PreparationItem.preparing` | `Hazırlanıyor` |
| `PreparationItem.ready` | `Teslim edildi` |

This disabled mode intentionally gives up item-level delivery proof. It exists for small operations that do not run ServiceStaffApp.

### Repeat Order

Customers may submit multiple orders during the same table visit.

After a successful order:

1. Customer can return to the menu.
2. Customer builds a new cart.
3. New submission requires fresh table presence again.
4. New order attaches to the same active TableSession if it is still open.

### Modify or Cancel Submitted Orders

Customers cannot directly modify or cancel submitted orders in the first version.

Changes, cancellations, refunds, discounts, or corrections must go through CashierApp or another explicitly authorized staff workflow.

## Error and Recovery States

CustomerApp must preserve customer trust when order submission cannot continue.

| Case | System Behavior | Customer UX |
| --- | --- | --- |
| Fresh presence expired | Reject submit until QR is refreshed | Preserve cart and ask for current QR scan |
| Product unavailable | Reject affected item server-side | Show item-level message and keep cart editable |
| Variant unavailable | Reject affected item server-side | Open item editor or show item-level message and keep cart editable |
| Cart pricing invalid | Reject affected item/server-side cart state | Keep cart editable and ask customer to review affected items |
| Required variant missing | Reject item | Open item editor with missing requirement |
| Required modifier missing | Reject item | Open item editor with missing requirement |
| Invalid modifier combination | Reject item | Show item-level correction message |
| TableSession closed | Do not attach to closed session | Require fresh QR and retry against current table state |
| Tenant suspended/unavailable | Reject customer actions | Show tenant unavailable message |
| Station unavailable | Reject or mark dependent products unavailable | Show affected products as unavailable |
| Duplicate submit | Return original order result | Do not create duplicate order |
| Network failure after submit | Retry by idempotency key | Show pending/retry state without duplicating order |

Price, variant, availability, table state, and station state must be rechecked server-side during order submission.

## Operational Safety

- QR token redemption must be atomic.
- A QR token can be redeemed only once.
- Concurrent redemption of the same token must allow only one winner.
- Order submission must be idempotent.
- Duplicate clicks on the order button must not create duplicate orders.
- The backend must not trust frontend prices, station IDs, table IDs, or totals.
- The backend must not trust frontend-provided TableSession IDs.
- Only one active TableSession may exist per tenant/table.
- Order item price snapshots must be created server-side at submission time.
- Product modifiers/options must be validated server-side.
- Product and variant availability must be checked server-side at submission time.
- Cart item notes must be persisted with the order item when allowed.
- If order creation fails halfway, no partial order should leak into station queues.
- If station queue creation is part of the same operation, it must be transactionally consistent with order creation.
- Successful order submission clears only the submitted cart. Failed submission preserves the cart.
- CustomerApp may show table orders only after fresh table presence verification.
- CustomerApp may show table bill and balance only after fresh table presence verification.
- Customer-visible totals must be calculated server-side.

## Integration Expectations

| Context / Module | Expected Use |
| --- | --- |
| Platform / Tenant Registry | Resolve tenant availability from subdomain |
| Tenant Setup / Venue Layout | Read table context after trusted QR/session resolution |
| Tenant Setup / Menu Catalog | Read customer menu, product variants/options, availability, and server-side price data |
| Ordering / Table Presence | Redeem QR and require fresh table presence |
| Ordering / Customer Ordering | Own CustomerOrderingSession, cart, idempotent order submission, My Orders, and Table Orders |
| Fulfillment / Preparation | Read customer-visible preparation state |
| Fulfillment / Service Delivery | Read delivered state when service delivery tracking is enabled |
| Settlement / Table Session and Billing | Read active table session, table bill, and remaining balance |
| Settlement / Payments | Read payment effects through bill/balance only; CustomerApp cannot create payments |

## Open Questions

None currently.
