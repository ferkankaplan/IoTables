# Module: Table Display Provisioning

## Purpose

Table Display Provisioning owns ESP32 table display firmware generation and credentials.

It lets TenantApp bind a physical table display to a table so the display can authenticate and fetch the current QR payload. It does not prove customer presence; that belongs to Ordering / Table Presence.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| TableDisplayCredential | Entity | issue, rotate, revoke |
| Display-to-table binding | Association | bind one active display credential to a table in the current release |
| Display credential authentication | Security rule | authenticate QR fetch requests |
| TableDisplayFirmwarePackage | One-time encrypted artifact | generate one `.ino` file per table with WiFi, tenant host, table label, TLS root CA, and raw display credential |

## Not Owned

- TableAccessToken generation or redemption.
- Fresh customer table presence.
- CustomerOrderingSession.
- Cart or order submission.
- Hall/table lifecycle, owned by Venue Layout.
- Device inventory, health checks, or connection logs in the current release.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| TenantApp / Tenant Admin | create table display firmware, revoke/re-provision display | Own tenant and physical table |
| ESP32 table display | fetch current QR payload | Must authenticate with active table display credential |
| Ordering / Table Presence | request token payload for authenticated display | Through public interface only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Generate display firmware | Create or rotate the active display credential and return one table `.ino` file once | TenantApp |
| Authenticate display credential | Resolve tenant/table for QR fetch | QR fetch endpoint, Table Presence |
| Revoke display credential | Disable a table display credential | TenantApp |

## Internal Rules

- In v1, the ESP32 is treated as the table display surface, not a separate device inventory aggregate.
- A display firmware package is generated as a one-time artifact.
- Firmware generation is atomic with credential rotation.
- Only one active table display credential exists per tenant/table in the current release.
- Re-provisioning revokes the previous active credential.
- The backend resolves tenant and table from the credential; it must not trust table IDs sent by the ESP32.
- Display credentials must never be embedded in customer QR payloads.
- WiFi passwords and raw display credentials may appear only in the one-time generated `.ino` response or its short-lived encrypted download artifact.
- Firmware generation is allowed only for `physical` tables. `virtual_test` tables, including permanent `x00` and `x99` slots, must never receive ESP32 display credentials or firmware.

## Operational Safety

- Store credential secrets as hashes, not raw values.
- Do not persist raw WiFi passwords or raw display credentials in database fields, logs, or audit events; the generated `.ino` may be retained only as a short-lived encrypted one-time artifact until download or expiry.
- Expired, consumed, revoked, disabled, or wrong-table credentials fail closed.
- Credential rotation must invalidate the old credential before the new credential is considered active.
- Provisioning/revocation must be audited.
- QR token fetch must not leak table credential material.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| TableDisplayCredential | active -> revoked/rotated | tenant, table, credentialHash, status, provisionedAt, revokedAt, lastSeenAt | Only one active display credential per tenant/table in the current release; backend resolves table from credential, not client-provided IDs; raw credential never appears in QR payload | Revoke/rotate instead of hard-delete; preserve safe metadata for audit/support |
| TableDisplayFirmwarePackage | generated -> downloaded / expired | tenant, table, generatedByUserId, credentialId, encryptedFirmwareRef, expiresAt, downloadedAt | One-time encrypted artifact; raw WiFi password and raw credential are never stored as queryable/plain fields | Preserve safe metadata only; delete encrypted `.ino` content after download or expiry |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Generate/download/revoke table display firmware from table detail panel |

## Future Service Boundary

- Own data: display credentials and one-time firmware package metadata.
- Own APIs: generate firmware, authenticate display, revoke credential.
- Published events: table_display.provisioned, table_display.revoked.
- Consumed events: table.disabled, tenant.suspended.
- Must not leak: raw display credentials, raw WiFi passwords, or generated firmware content.

## Open Questions

None currently.
