# Module Contracts: Customer Ordering

Source module: [customer-ordering.md](customer-ordering.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `customer_ordering.attach_or_refresh_session` | Table Presence | tenantId, tableId, optional cookie token, presence expiry | Called only after valid QR redemption; compatible existing session preferred | Create or update CustomerOrderingSession; cart is preserved when compatible | CustomerOrderingSession and cookie token |
| `customer_ordering.add_or_update_cart_item` | CustomerApp | session cookie, clientCartItemId, product/variant/modifiers, quantity, note | Valid customer session; menu item validated through Menu Catalog; client price ignored | Upsert cart item by `clientCartItemId`; one active cart per session | Active cart |
| `customer_ordering.remove_cart_item` | CustomerApp | session cookie, clientCartItemId | Valid customer session; active cart | Remove item or set quantity zero; idempotent if already absent | Active cart |
| `customer_ordering.submit_order` | CustomerApp | session cookie, idempotency key, cart snapshot/API-computed request hash | Fresh table presence; active non-empty cart; tenant/table active; menu revalidated server-side | Reserve idempotency row; lock cart and table session path; create Order/OrderItems; call Settlement and Preparation contracts; duplicate key returns original result | Submitted order, cleared/submitted cart, table session/check linkage |
| `customer_ordering.abandon_cart` | CustomerApp, retention job | session/cart | Session owner or retention policy | Mark cart abandoned; not billable | Abandoned cart |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `customer_ordering.get_cart` | CustomerApp | session cookie | Session owner | Active cart with estimated display totals |
| `customer_ordering.list_my_orders` | CustomerApp | session cookie | Session owner; does not require new order session per order | Orders submitted by this CustomerOrderingSession |
| `customer_ordering.list_table_orders` | CustomerApp, CashierApp | tableSessionId or fresh customer table context | CustomerApp requires fresh presence; Cashier requires cashier permission | Orders for active table session |
| `customer_ordering.read_order_item_routing` | StationStaffApp, ServiceStaffApp, Fulfillment | orderItemId/filter | Staff scope enforced by Fulfillment/Access | Order item snapshot and routing metadata |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `table_presence.require_fresh_presence` | Gate submit and table visibility. |
| `menu_catalog.validate_cart_item` | Validate product, variant, modifiers, availability, station. |
| `menu_catalog.price_cart_item` | Create server-side price snapshots. |
| `table_session_billing.open_session_check_if_needed` | Attach order to active TableSession/Check. |
| `preparation.create_queue_item` | Route each OrderItem to station queue. |
| `audit.record_event` | Record order submission. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `order.submitted` | Order transaction commits | Preparation, CashierApp read models, Audit |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `fresh_presence_required` | Customer must scan current QR before submit/table visibility. |
| `empty_cart` | No active cart items can be submitted. |
| `cart_changed_conflict` | Idempotency key reused with different request/cart hash. |
| `item_not_orderable` | Menu validation failed during submit. |
| `closed_table_session` | Target table session cannot accept new orders. |
