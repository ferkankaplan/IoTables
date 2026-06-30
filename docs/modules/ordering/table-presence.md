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

- TableDisplayClaim or TableDisplayCredential.
- Hall/table setup data.
- Customer cart contents.
- Order creation.
- TableSession billing.
- Payments or session closure.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| ESP32 table display | fetch QR payload after display authentication | Table context comes from Table Display Provisioning |
| CustomerApp | redeem table access token | Token must be valid, unexpired, unused, and table-matching |
| Customer Ordering | require fresh presence for submit and table visibility | Server-side check only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Issue current QR token | Return current token payload for authenticated table display | ESP32 table display |
| Redeem table access token | Create or refresh customer presence | CustomerApp |
| Require fresh presence | Guard order submit and table orders/balance visibility | Customer Ordering |
| Rotate token after redemption | Prevent replay after successful scan | QR display flow |

## Internal Rules

- QR token lifetime is 60 seconds in v1.
- QR token is one-time use.
- Token redemption is atomic.
- Token must not expose trusted table IDs directly.
- Redeeming a token refreshes an existing compatible CustomerOrderingSession when possible.
- Fresh table presence is required for CustomerApp order submission and table-order/balance visibility.
- Token rotation in v1 is poll-based: after redemption, the next ESP32 fetch returns a fresh token.
- Push, SSE, or WebSocket display updates are out of scope for v1.

## Operational Safety

- Concurrent redemption of the same token must allow only one winner.
- Store token data in replay-safe hashed form.
- Expired or consumed tokens fail closed.
- Wrong-table redemption must not change the current customer session.
- Token rotation must not create duplicate or conflicting active tokens for the same table display.
- The backend must recheck tenant status and table enabled state before granting presence.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| TableAccessToken | Stores generated token metadata | tenant, table, tokenHash, expiresAt, consumedAt |
| CustomerOrderingSession presence fields | Stores fresh presence window | `presenceValidUntil`, refreshed after valid redemption |

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
