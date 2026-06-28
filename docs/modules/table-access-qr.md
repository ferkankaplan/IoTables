# Module: Table Access / QR

## Purpose

Table Access / QR owns the secure physical table presence mechanism.

It proves that an anonymous browser recently scanned the current QR displayed on a table's ESP32 screen. It does not create orders, manage carts, or own table billing sessions.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| TableAccessToken | Token | generate, expire, consume |
| Fresh table presence | State | grant and refresh presence window |
| Table display QR flow | Workflow | provide current QR to the table display |
| QR replay prevention | Safety rule | reject reused, expired, or wrong-table tokens |

## Not Owned

- Customer cart.
- Order creation.
- TableSession billing.
- Tenant setup.
- Product/menu data.
- Payment or session closure.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| ESP32 table display | Read current QR/token payload | Own table only |
| CustomerApp | Redeem token | Token must be valid, unexpired, unused, and table-matching |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Fetch current table QR | Let ESP32 display the current QR | ESP32 table display |
| Redeem table access token | Create or refresh CustomerOrderingSession presence | CustomerApp |
| Rotate token after redemption | Prevent reuse after successful scan | CustomerApp / display flow |

## Internal Rules

- QR token must be short-lived.
- QR token must be one-time use.
- Token redemption must be atomic.
- Token must not expose trusted table IDs directly.
- Fresh table presence is required for CustomerApp order submission and table-order/balance visibility.
- Redeeming a token refreshes an existing compatible CustomerOrderingSession when possible.

## Operational Safety

- Concurrent redemption of the same token must allow only one winner.
- Token data should be stored in a replay-safe form.
- Expired or consumed tokens must fail closed.
- Wrong-table token redemption must not change the current customer session.
- Token rotation must not create duplicate or conflicting active tokens for the same table display.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| TableAccessToken | Stores generated token metadata | token hash, tenant, table, expiresAt, consumedAt |
| CustomerOrderingSession presence fields | Stores `presenceValidUntil` | Owned by Customer Ordering, updated through this module's redeem flow |

## App Surfaces

| App | Usage |
| --- | --- |
| CustomerApp | Redeems QR and requires fresh table presence |
| TenantApp | Configures halls/tables that will have display QR behavior |

## Future Service Boundary

- Own data: table access tokens and display token state.
- Own APIs: token generation, display QR fetch, token redemption.
- Published events: table_access_token.redeemed.
- Consumed events: table disabled, tenant suspended.
- Must not leak: raw token secrets or device credentials.

## Open Questions

- Exact ESP32 authentication/provisioning flow.
- Whether token rotation is poll-only or uses push/SSE/WebSocket later.
