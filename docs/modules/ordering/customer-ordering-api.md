# API Contracts: Customer Ordering

Source contracts: [customer-ordering-contracts.md](customer-ordering-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Customer Ordering owns anonymous customer sessions, carts, order submission, order records, and customer/table order visibility.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/customer/cart` | CustomerApp | `customer_ordering.get_cart` | Customer session cookie | none | `Cart` | `session_expired` |
| `POST` | `/api/v1/customer/cart/items` | CustomerApp | `customer_ordering.add_or_update_cart_item` | Customer session cookie + CSRF | Body: `CartItemWriteRequest` | `Cart` | `item_not_orderable`, `variant_invalid`, `station_unavailable` |
| `POST` | `/api/v1/customer/cart/items/{clientCartItemId}/remove` | CustomerApp | `customer_ordering.remove_cart_item` | Customer session cookie + CSRF | Path: `clientCartItemId` | `Cart` | `session_expired` |
| `POST` | `/api/v1/customer/cart/abandon` | CustomerApp | `customer_ordering.abandon_cart` | Customer session cookie + CSRF | none | `CartAbandonedResult` | `session_expired` |
| `POST` | `/api/v1/customer/orders` | CustomerApp | `customer_ordering.submit_order` | Customer session cookie + CSRF + `Idempotency-Key` | Body: `SubmitOrderRequest` | `SubmittedOrderResult` | `fresh_presence_required`, `empty_cart`, `cart_changed_conflict`, `item_not_orderable`, `closed_table_session` |
| `GET` | `/api/v1/customer/orders/my` | CustomerApp | `customer_ordering.list_my_orders` | Customer session cookie | none | `CustomerOrderList` | `session_expired` |
| `GET` | `/api/v1/customer/table-orders` | CustomerApp | `customer_ordering.list_table_orders` | Customer session cookie + fresh presence | Optional query: `tableSessionId` only if it matches the fresh table context | `CustomerOrderList` | `fresh_presence_required` |
| `GET` | `/api/v1/cashier/table-sessions/{tableSessionId}/orders` | CashierApp | `customer_ordering.list_table_orders` | Cashier session | Path: `tableSessionId` | `CashierOrderList` | `missing_role`, `not_found_or_hidden` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `customer_ordering.attach_or_refresh_session` | Called by Table Presence after QR redemption. |
| `customer_ordering.read_order_item_routing` | Called by Fulfillment/Service Delivery. |

## Request Schemas

`CartItemWriteRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `clientCartItemId` | string | yes | Stable client-generated item key for upsert. |
| `productId` | string | yes | Product to order. |
| `variantId` | string | yes | Variant/portion. |
| `modifierOptionIds` | string array | no | Validated against modifier bounds. |
| `quantity` | integer | yes | Quantity greater than zero. |
| `note` | string | no | Customer note; sanitized and length-limited. |

`SubmitOrderRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `cartVersion` | string/integer | yes | Client's last displayed cart version. |
| `cartItemIds` | string array | yes | Submitted cart item keys. |

The `Idempotency-Key` header is required for submit. The API layer computes the normalized request hash from server-trusted session/cart/request data. The body must not include trusted prices, totals, or a client-controlled request hash.

## Response Schemas

`Cart` includes `cartId`, `version`, `items`, `displaySubtotalMinor`, `currency`, and `updatedAt`. Display totals are estimates; server recalculates on submit.

`SubmittedOrderResult`:

| Field | Type | Notes |
| --- | --- | --- |
| `orderId` | string | Created or replayed order. |
| `tableSessionId` | string | Active table session. |
| `checkId` | string | V1 adisyon/check. |
| `items` | array | Submitted order item snapshots. |
| `cartCleared` | boolean | True after successful submit. |
| `duplicate` | boolean | True when returned from compatible idempotent replay. |

`CustomerOrderList` returns orders with customer-visible preparation/delivery status, item labels, quantities, notes, order time, and server price snapshots. `CashierOrderList` may include correction/void eligibility fields.

## Idempotency

`POST /api/v1/customer/orders` requires `Idempotency-Key`.

Scope the key by `tenantId + customerOrderingSessionId + route + idempotencyKey`. Same key and same request returns the original order result. Same key and different request returns `409 idempotency_conflict`.
