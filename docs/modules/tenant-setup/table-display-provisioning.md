# Module: Table Display Provisioning

## Purpose

Table Display Provisioning owns ESP32 table display claims and credentials.

It lets TenantApp bind a physical table display to a table so the display can authenticate and fetch the current QR payload. It does not prove customer presence; that belongs to Ordering / Table Presence.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| TableDisplayClaim | Entity | create, expire, consume |
| TableDisplayCredential | Entity | issue, rotate, revoke |
| Display-to-table binding | Association | bind one active display credential to a table in v1 |
| Display credential authentication | Security rule | authenticate QR fetch requests |

## Not Owned

- TableAccessToken generation or redemption.
- Fresh customer table presence.
- CustomerOrderingSession.
- Cart or order submission.
- Hall/table lifecycle, owned by Venue Layout.
- Device inventory, firmware, health checks, or connection logs in v1.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| TenantApp / Tenant Admin | create display claim, revoke/re-provision display | Own tenant and table |
| ESP32 table display | fetch current QR payload | Must authenticate with active table display credential |
| Ordering / Table Presence | request token payload for authenticated display | Through public interface only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Create display claim | Start one-time provisioning for a table | TenantApp |
| Consume display claim | Exchange claim for table display credential | ESP32 setup flow |
| Authenticate display credential | Resolve tenant/table for QR fetch | QR fetch endpoint, Table Presence |
| Revoke display credential | Disable a table display credential | TenantApp |

## Internal Rules

- In v1, the ESP32 is treated as the table display surface, not a separate device inventory aggregate.
- A display claim is short-lived and one-time use.
- Claim consumption is atomic.
- Only one active table display credential exists per tenant/table in v1.
- Re-provisioning revokes the previous active credential.
- The backend resolves tenant and table from the credential; it must not trust table IDs sent by the ESP32.
- Display credentials must never be embedded in customer QR payloads.

## Operational Safety

- Store claim and credential secrets as hashes, not raw values.
- Expired, consumed, revoked, disabled, or wrong-table credentials fail closed.
- Credential rotation must invalidate the old credential before the new credential is considered active.
- Provisioning/revocation must be audited.
- QR token fetch must not leak table credential material.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| TableDisplayClaim | created -> consumed / expired | tenant, table, claimHash, createdByUserId, expiresAt, consumedAt | Claim is one-time use; claim secret stored hashed; consuming a claim is atomic and creates/rotates credential | Preserve consumed/expired claim metadata for provisioning audit; never store raw claim |
| TableDisplayCredential | active -> revoked/rotated | tenant, table, credentialHash, status, provisionedAt, revokedAt, lastSeenAt | Only one active display credential per tenant/table in v1; backend resolves table from credential, not client-provided IDs; raw credential never appears in QR payload | Revoke/rotate instead of hard-delete; preserve safe metadata for audit/support |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Provision/revoke table display from table detail panel |

## Future Service Boundary

- Own data: display claims and display credentials.
- Own APIs: create claim, consume claim, authenticate display, revoke credential.
- Published events: table_display.provisioned, table_display.revoked.
- Consumed events: table.disabled, tenant.suspended.
- Must not leak: raw display credentials or claim secrets.

## Open Questions

None currently.
