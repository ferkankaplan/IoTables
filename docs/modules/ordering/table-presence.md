# Module: Table Presence

## Purpose

Table Presence owns short-lived QR tokens and fresh table presence for anonymous CustomerApp sessions.

It proves that a browser recently scanned the current QR displayed at a table. It does not provision the ESP32 display credential; that belongs to Tenant Setup / Table Display Provisioning.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| TableAccessToken | Entity | generate, expire, consume |
| Fresh table presence | State | grant and refresh presence window |
| QR replay prevention | Security rule | reject reused, expired, or wrong-table tokens |
| Presence-to-customer-session update | Workflow | refresh compatible CustomerOrderingSession |

## Not Owned

- TableDisplayFirmwarePackage or TableDisplayCredential.
- Hall/table setup data.
- Customer cart contents.
- Order creation.
- TableSession billing.
- Payments or session closure.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| ESP32 table display | fetch QR payload after display authentication | Table context comes from Table Display Provisioning |
| CashierApp | request QR preview for virtual test tables | Only `virtual_test` tables; physical tables are forbidden |
| CustomerApp | redeem table access token | Token must be valid, unexpired, unused, and table-matching |
| Customer Ordering | require fresh presence for submit and table visibility | Server-side check only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Issue current QR token | Return current token payload for authenticated table display | ESP32 table display |
| Issue virtual table QR preview | Return current token payload for cashier-visible virtual test table | CashierApp |
| Redeem table access token | Create or refresh customer presence | CustomerApp |
| Require fresh presence | Guard order submit and table orders/balance visibility | Customer Ordering |
| Rotate token after redemption | Prevent replay after successful scan | QR display flow |

## Internal Rules

- QR token lifetime is 60 seconds in the current release.
- QR token is one-time use.
- Token redemption is atomic.
- Token must not expose trusted table IDs directly.
- Redeeming a token refreshes an existing compatible CustomerOrderingSession when possible.
- Fresh table presence is required for CustomerApp order submission and table-order/balance visibility.
- Token rotation in the current release is poll-based: after redemption, the next ESP32 fetch returns a fresh token.
- Cashier QR preview is allowed only for `virtual_test` tables. It must fail closed for physical tables, disabled tables, or tenant mismatch.
- Push, SSE, or WebSocket display updates are out of scope for the current release.

## Operational Safety

- Concurrent redemption of the same token must allow only one winner.
- Store token data in replay-safe hashed form.
- Expired or consumed tokens fail closed.
- Wrong-table redemption must not change the current customer session.
- Token rotation must not create duplicate or conflicting active tokens for the same table display.
- The backend must recheck tenant status and table enabled state before granting presence.
- Cashier QR preview must recheck that the table is `virtual_test`; it must never bypass ESP32 presence for physical tables.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| TableAccessToken | issued -> consumed / expired | tenant, table, tokenHash, expiresAt, consumedAt | Token is one-time use; token secret stored hashed; redemption is atomic; token does not expose trusted table IDs | Expired/consumed tokens can be retained short-term for replay investigation, then purged by retention policy |
| CustomerOrderingSession presence fields | refreshed while session active -> expired | customerOrderingSession, presenceValidUntil, lastRedeemedToken metadata if needed | Fresh presence gates order submit and table order/balance visibility; browsing can continue without fresh presence | Presence expiry does not delete cart; CustomerOrderingSession lifecycle is owned by Customer Ordering |

## App Surfaces

| App | Usage |
| --- | --- |
| CustomerApp | Redeems QR and requires fresh table presence |

## Future Service Boundary

- Own data: table access tokens and presence refresh state.
- Own APIs: issue token payload, redeem token, check fresh presence.
- Published events: table_access_token.redeemed.
- Consumed events: display credential authenticated, table.disabled, tenant.suspended.
- Must not leak: trusted table resolution to customer input.

## Open Questions

None currently.
