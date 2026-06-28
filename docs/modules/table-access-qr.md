# Module: Table Access / QR

## Purpose

Table Access / QR owns the secure physical table presence mechanism.

It proves that an anonymous browser recently scanned the current QR displayed on a table's ESP32 screen. It does not create orders, manage carts, or own table billing sessions.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| TableAccessToken | Token | generate, expire, consume |
| Table display credential | Credential | authenticate a table-bound ESP32 display |
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
| ESP32 table display | Read current QR/token payload | Authenticated with the table's active display credential |
| CustomerApp | Redeem token | Token must be valid, unexpired, unused, and table-matching |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Provision table display | Create a one-time table display claim | TenantApp |
| Fetch current table QR | Let ESP32 display the current QR | ESP32 table display |
| Redeem table access token | Create or refresh CustomerOrderingSession presence | CustomerApp |
| Rotate token after redemption | Prevent reuse after successful scan | CustomerApp / display flow |

## ESP32 Provisioning and Auth

In v1, the ESP32 screen is not modeled as a separate device inventory aggregate. It is treated as the display surface of a Table.

Provisioning flow:

1. Tenant Admin opens a table detail panel in TenantApp.
2. TenantApp creates a one-time, short-lived display claim for that table.
3. The ESP32 setup flow submits the claim to the backend.
4. The backend consumes the claim atomically and returns a table display credential once.
5. The ESP32 stores the credential locally and uses it to fetch the current QR for that table.

Auth rules:

- The ESP32 must authenticate with a table display credential before receiving a QR payload.
- The backend resolves tenant and table from the credential; it must not trust table IDs sent by the ESP32.
- Only one active table display credential exists per table in v1.
- Re-provisioning a table display rotates the credential and revokes the previous active credential.
- Revoked, disabled, or wrong-table credentials must fail closed.
- Table display credentials are not customer QR tokens and must never be embedded in QR payloads.

Token rotation in v1 is poll-based. The ESP32 fetches the current QR periodically, and after a customer redeems a QR the next fetch returns a fresh token. Push, SSE, or WebSocket display updates are out of scope for v1.

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
- Table display claim consumption must be atomic and one-time.
- Table display credential rotation must invalidate the old credential before the new credential is considered active.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| TableDisplayClaim | One-time provisioning claim for a table display | tenant, table, claim hash, expiresAt, consumedAt |
| TableDisplayCredential | Authenticates the ESP32 display for a table | tenant, table, credential hash, active/revoked state |
| TableAccessToken | Stores generated token metadata | token hash, tenant, table, expiresAt, consumedAt |
| CustomerOrderingSession presence fields | Stores `presenceValidUntil` | Owned by Customer Ordering, updated through this module's redeem flow |

## App Surfaces

| App | Usage |
| --- | --- |
| CustomerApp | Redeems QR and requires fresh table presence |
| TenantApp | Configures halls/tables that will have display QR behavior |

## Future Service Boundary

- Own data: table display claims, display credentials, table access tokens, and display token state.
- Own APIs: table display provisioning, token generation, display QR fetch, token redemption.
- Published events: table_access_token.redeemed.
- Consumed events: table disabled, tenant suspended.
- Must not leak: raw token secrets or device credentials.

## Open Questions

None currently.
