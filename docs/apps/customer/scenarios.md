# CustomerApp Scenarios
### C-01: Redeem Fresh QR

Happy path:

1. Customer scans current QR.
2. CustomerApp submits TableAccessToken.
3. Backend validates token hash, expiry, tenant/table, and consumed state.
4. Backend consumes token atomically.
5. Backend creates or refreshes CustomerOrderingSession.
6. Backend sets `presenceValidUntil`.
7. CustomerApp opens menu.

Branches:

| Branch | Expected Result |
| --- | --- |
| Token expired | Ask customer to scan current QR |
| Token already consumed | Ask customer to scan current QR |
| Token belongs to another table | Reject and ask customer to scan own table QR |
| Tenant suspended | Show tenant unavailable |
| Table disabled | Reject ordering for table |
| Existing CustomerOrderingSession same tenant/table | Refresh same session |
| Existing CustomerOrderingSession another tenant/table | Do not silently transfer cart; require correct QR/session context |
| Browser rejects cookie | Customer may browse only if implementation allows stateless preview; ordering cannot proceed without server session |

Result:

- Customer has a valid anonymous session and fresh table presence.

Ownership:

- CustomerApp + Ordering / Table Presence.

### C-02: Browse Menu and Build Cart

Happy path:

1. Customer browses categories and products.
2. Customer opens product detail panel.
3. Customer selects required variant/portion when applicable and required modifiers/options.
4. Customer adds item to cart.
5. Customer edits quantity, note, variant, and modifiers before submission.

Branches:

| Branch | Expected Result |
| --- | --- |
| Product unavailable | Product is not orderable |
| Product disabled | Product is not orderable |
| Variant unavailable | Variant is not orderable |
| Variant disabled | Variant is not orderable |
| Required variant missing | Add-to-cart is blocked |
| Required modifier missing | Add-to-cart is blocked |
| Invalid modifier combination | Add-to-cart is blocked |
| Quantity invalid | Add-to-cart/update is blocked |
| Fresh presence expires while browsing | Browsing can continue; submit will require fresh QR |
| CustomerOrderingSession expires | Cart may be lost; fresh QR can create a new session |
| Browser refreshes page | Cart is restored while server session/cookie remains valid |

Result:

- Cart remains non-billable and owned by CustomerOrderingSession.

Ownership:

- CustomerApp + Customer Session and Cart + Menu Catalog read.

### C-03: Submit First Order at Empty Table

Happy path:

1. Customer submits cart with idempotency key.
2. Backend validates session, fresh presence, cart, menu product variants/modifiers/availability, table, and tenant.
3. Backend creates new TableSession because no active session exists.
4. Backend creates one Check/Adisyon for the TableSession.
5. Backend creates Order, OrderItems, product/variant/price/modifier snapshots, and PreparationItems.
6. Backend commits transaction.
7. CustomerApp clears submitted cart and shows confirmation.

Branches:

| Branch | Expected Result |
| --- | --- |
| Fresh presence expired | Preserve cart and require fresh QR |
| Cart empty | Reject submit |
| Product unavailable at submit | Reject affected item and preserve cart |
| Variant unavailable at submit | Reject affected item and preserve cart |
| Modifier invalid at submit | Reject affected item and preserve cart |
| Table disabled at submit | Reject and preserve cart where useful |
| Tenant suspended at submit | Reject and show unavailable |
| Concurrent first order creates TableSession first | Use existing active TableSession or retry safely; never create two active sessions |
| Transaction fails after partial work | Roll back; no partial order visible |
| Duplicate idempotency key same request | Return original result |
| Duplicate idempotency key different request | Fail closed |

Result:

- One active TableSession, one Check, and one accepted order exist.

Ownership:

- CustomerApp + Ordering + Settlement command + Fulfillment.

### C-04: Submit Additional Order at Active Table

Happy path:

1. Customer scans fresh QR or still has fresh presence.
2. Customer builds another cart.
3. Backend attaches new order to current active TableSession.
4. My Orders shows all orders from that CustomerOrderingSession.
5. Table Orders shows all orders in active TableSession after fresh presence.

Branches:

| Branch | Expected Result |
| --- | --- |
| Same browser/session orders again | My Orders shows both orders |
| Different browser at same table orders | Order joins same TableSession; not shown in first browser's My Orders |
| Browser cookie deleted | My Orders from old session is lost; Table Orders can be shown after fresh QR |
| TableSession closes before submit | Require fresh QR and attach to current active/new TableSession only if table can accept orders |

Result:

- Multiple CustomerOrderingSessions may contribute orders to one TableSession.

Ownership:

- CustomerApp + Ordering + Settlement.

### C-05: View My Orders, Table Orders, and Bill

Happy path:

1. Customer opens My Orders.
2. CustomerApp shows orders from current CustomerOrderingSession.
3. Customer verifies fresh presence for Table Orders or bill.
4. CustomerApp shows active TableSession orders and read-only bill/balance.

Branches:

| Branch | Expected Result |
| --- | --- |
| Fresh presence missing for Table Orders | Ask customer to scan current QR |
| Cookie lost | My Orders may be lost; Table Orders can recover after fresh QR |
| TableSession closed | Current customer cannot mutate it; new order requires fresh QR and current table state |
| Payment recorded by cashier | Bill/balance updates read-only |
| Payment voided by cashier | Bill/balance updates read-only |
| Item voided by cashier | Order/bill state updates read-only |

Result:

- Customer can inspect but not mutate billing or submitted orders.

Ownership:

- CustomerApp + Ordering read + Settlement read.
