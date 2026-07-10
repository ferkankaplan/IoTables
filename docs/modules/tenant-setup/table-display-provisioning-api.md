# API Contracts: Table Display Provisioning

Source contracts: [table-display-provisioning-contracts.md](table-display-provisioning-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Table Display Provisioning owns ESP32 firmware generation, display credentials, credential revocation, and display status. The device is a table display surface only.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/api/tenant-setup/tables/{tableId}/display-firmware` | TenantApp | `table_display.generate_firmware` | Tenant Admin session + CSRF | Body: `wifiSsid`, `wifiPassword` | `DisplayFirmwareCreated` with one-time `firmwareContent` | `not_authorized`, `not_found_or_hidden`, `wifi_required` |
| `GET` | `/api/tenant-setup/tables/{tableId}/display-state` | TenantApp | `table_display.get_display_state` | Tenant Admin session | Path: `tableId` | `DisplayState` | `not_authorized`, `not_found_or_hidden` |
| `POST` | `/api/tenant-setup/tables/{tableId}/display-credential/revoke` | TenantApp | `table_display.revoke_credential` | Tenant Admin session + CSRF | Body: `reason` | `DisplayState` | `reason_required`, `not_found_or_hidden` |
| `POST` | `/api/tenant-setup/tables/{tableId}/display-credential/rotate` | TenantApp | `table_display.rotate_credential` | Tenant Admin session + CSRF | Body: `reason` | `DisplayState` | `reason_required`, `not_found_or_hidden` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `table_display.authenticate_credential` | Used as the authentication guard for QR fetch endpoints in Table Presence. |

## Request Schemas

`DisplayFirmwareCreateRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `wifiSsid` | string | yes | Rendered into the one-time `.ino` response; never logged. |
| `wifiPassword` | string | yes | Rendered into the one-time `.ino` response; never persisted raw or logged. |

## Response Schemas

`DisplayFirmwareCreated`:

| Field | Type | Notes |
| --- | --- | --- |
| `firmwareId` | string | One-time artifact identifier. |
| `fileName` | string | Generated file name, for example `masa000.ino`. |
| `credentialId` | string | Credential identifier. |
| `tableId` | string | Bound table. |
| `expiresAt` | timestamp | Short-lived download expiry. |
| `firmwareContent` | string | One-time `.ino` file content. Contains raw WiFi and display credential secrets and must not be logged or recoverable later. |

`DisplayState` includes `tableId`, `activeCredentialId?`, `credentialStatus`, `lastIssuedAt?`, `lastRevokedAt?`, `pendingFirmwareId?`, `pendingFirmwareExpiresAt?`, and `lastFirmwareDownloadedAt?`. It never includes raw WiFi passwords, raw credentials, or generated firmware content.

## Idempotency

Firmware generation is state-guarded by table credential locking: generating a new firmware package rotates the display credential and revokes the previous active credential in the same transaction. The generated `.ino` content is returned once in the response and is not persisted as recoverable raw content. Credential revocation and rotation are state-guarded and audited; no `Idempotency-Key` is required in the current release.
