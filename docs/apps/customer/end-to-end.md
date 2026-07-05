# CustomerApp End-to-End Role

This document extracts the parts of the shared current release end-to-end flow where this app participates.

See the full shared flow: [../_shared/master-end-to-end.md](../_shared/master-end-to-end.md).

### 4. Customer Scans QR and Builds Cart
1. Customer scans the current QR on the table display.
2. CustomerApp redeems the TableAccessToken.
3. Backend atomically consumes the token.
4. Backend creates or refreshes a compatible CustomerOrderingSession.
5. Backend sets fresh table presence for 2 minutes.
6. Customer browses the menu and builds a cart.
7. Cart belongs to CustomerOrderingSession, not TableSession.

Acceptance criteria:

- Reused, expired, wrong-table, or already consumed QR tokens fail closed.
- A fresh QR refreshes an existing compatible CustomerOrderingSession when possible.
- CustomerOrderingSession can submit multiple orders while valid.
- Menu browsing can continue after fresh presence expires, but order submission cannot.
- Cart survives fresh QR re-verification while the CustomerOrderingSession remains recoverable.

### 5. Customer Submits Order
1. Customer taps order submit.
2. Frontend sends cart with an idempotency key.
3. Backend validates CustomerOrderingSession, tenant, table, fresh presence, cart, products, variants, modifiers, availability, and quantities.
4. Backend recalculates prices server-side.
5. Backend opens or selects the active TableSession and single Check/Adisyon through Settlement.
6. Backend joins CustomerOrderingSession to the current TableSession.
7. Backend creates Order and OrderItems with product/variant/price/modifier/station snapshots.
8. Backend creates PreparationItems for station queues.
9. Backend commits all order submission records in one transaction.
10. CustomerApp clears only the submitted cart and shows confirmation.

Acceptance criteria:

- Duplicate submit with the same idempotency key does not create duplicate orders.
- Failed order submission preserves the cart.
- No partial order appears in station, service, cashier, or customer history.
- Frontend prices and totals are informational only.
- The current release has no separate customer price-confirmation step.
- CustomerApp cannot modify or cancel submitted orders.

### 8. Customer Views Orders and Bill
1. CustomerApp shows My Orders from the current CustomerOrderingSession.
2. CustomerApp can show Table Orders for the active TableSession after fresh presence verification.
3. CustomerApp can show read-only bill/balance summary after fresh presence verification.
4. CustomerApp cannot create payments, close sessions, discount, cancel, refund, or mutate billable records.

Acceptance criteria:

- My Orders shows all orders submitted by the same CustomerOrderingSession.
- Table Orders can recover visibility after cookie loss only through fresh QR presence.
- Bill and balance are calculated server-side.
- Customer-visible status depends on service delivery tracking mode.
