# Table Access QR Flow

## Purpose

This document describes the end-to-end QR flow across two internal modules:

- [Tenant Setup / Table Display Provisioning](../tenant-setup/table-display-provisioning.md) owns ESP32 table display claims and credentials.
- [Ordering / Table Presence](../ordering/table-presence.md) owns short-lived customer QR tokens and fresh table presence.

Together they prove that an anonymous browser recently scanned the current QR displayed on a table's ESP32 screen.

This is not an owning module. The owning modules above define data ownership and implementation boundaries.

## Cross-Module Responsibilities

| Concept | Owning Module | Authority |
| --- | --- | --- |
| TableDisplayClaim | Tenant Setup / Table Display Provisioning | one-time display provisioning claim |
| TableDisplayCredential | Tenant Setup / Table Display Provisioning | authenticate a table-bound ESP32 display |
| TableAccessToken | Ordering / Table Presence | generate, expire, consume |
| Fresh table presence | Ordering / Table Presence | grant and refresh CustomerOrderingSession presence window |
| QR replay prevention | Ordering / Table Presence | reject reused, expired, or wrong-table tokens |

## Not Owned

- Customer cart.
- Order creation.
- TableSession billing.
- Hall/table setup data, owned by Venue Layout.
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
- Only one active table display credential exists per table in the current release.
- Re-provisioning a table display rotates the credential and revokes the previous active credential.
- Revoked, disabled, or wrong-table credentials must fail closed.
- Table display credentials are not customer QR tokens and must never be embedded in QR payloads.

Token rotation in the current release is poll-based. The ESP32 fetches the current QR periodically, and after a customer redeems a QR the next fetch returns a fresh token. Push, SSE, or WebSocket display updates are out of scope for the current release.

## Flow Rules

- Table display provisioning and table presence are separate internal modules/packages.
- QR token safety rules are owned by [Table Presence](../ordering/table-presence.md).
- ESP32 credential safety rules are owned by [Table Display Provisioning](../tenant-setup/table-display-provisioning.md).
- Fresh table presence is required for CustomerApp order submission and table-order/balance visibility.

## Operational Safety

- Concurrent redemption of the same token must allow only one winner.
- Token data should be stored in a replay-safe form.
- Expired or consumed tokens must fail closed.
- Wrong-table token redemption must not change the current customer session.
- Token rotation must not create duplicate or conflicting active tokens for the same table display.
- Table display claim consumption must be atomic and one-time.
- Table display credential rotation must invalidate the old credential before the new credential is considered active.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| TableDisplayClaim | created -> consumed / expired | tenant, table, claimHash, createdByUserId, expiresAt, consumedAt | One-time claim; atomic consumption; raw claim is never stored | Owned by Tenant Setup / Table Display Provisioning; retain safe metadata for provisioning audit |
| TableDisplayCredential | active -> revoked / rotated | tenant, table, credentialHash, status, provisionedAt, revokedAt, lastSeenAt | One active credential per tenant/table in the current release; backend resolves table from credential; raw credential never appears in QR payload | Owned by Tenant Setup / Table Display Provisioning; revoke/rotate instead of hard-delete |
| TableAccessToken | issued -> consumed / expired | tenant, table, tokenHash, expiresAt, consumedAt | One-time token; hashed token storage; redemption is atomic; token does not expose trusted table IDs | Owned by Ordering / Table Presence; retain short-term for replay investigation, then purge by retention policy |
| CustomerOrderingSession presence fields | refreshed while session active -> expired | customerOrderingSession, presenceValidUntil, lastRedeemedToken metadata if needed | Fresh presence gates order submit and table order/balance visibility; expiry does not delete cart | CustomerOrderingSession lifecycle is owned by Customer Ordering; presence refresh is controlled by Ordering / Table Presence |

## App Surfaces

| App | Usage |
| --- | --- |
| CustomerApp | Redeems QR and requires fresh table presence |
| TenantApp | Configures halls/tables that will have display QR behavior |

## Future Service Boundary

- Tenant Setup owns data/APIs for table display claims and credentials.
- Ordering owns data/APIs for table access tokens, token generation, display QR fetch, and token redemption.
- Published events: table_access_token.redeemed.
- Consumed events: table disabled, tenant suspended.
- Must not leak: raw token secrets or device credentials.

## Open Questions

None currently.
