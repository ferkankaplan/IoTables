# API Contracts: Table Display Provisioning

Source contracts: [table-display-provisioning-contracts.md](table-display-provisioning-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Table Display Provisioning owns ESP32 firmware generation, display credentials, credential revocation, and display status. The device is a table display surface only.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/api/tenant-setup/tables/{tableId}/display-firmware` | TenantApp | `table_display.generate_firmware` | Tenant Admin session + CSRF | Body: `wifiSsid`, `wifiPassword` | `DisplayFirmwareCreated` | `not_authorized`, `not_found_or_hidden`, `wifi_required` |
| `GET` | `/api/tenant-setup/tables/{tableId}/display-firmware/{firmwareId}/download` | TenantApp | `table_display.download_firmware` | Tenant Admin session + one-time download token | Query: `downloadToken` | `text/x-arduino` attachment | `firmware_download_expired`, `firmware_download_consumed`, `not_authorized` |
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
| `downloadUrl` | string | One-time download URL scoped to the current Tenant Admin session. |
| `downloadToken` | string | Returned once; required by the download URL; stored hashed server-side. |
| `credentialId` | string | Credential identifier. |
| `tableId` | string | Bound table. |
| `expiresAt` | timestamp | Short-lived download expiry. |

`DisplayState` includes `tableId`, `activeCredentialId?`, `credentialStatus`, `lastIssuedAt?`, `lastRevokedAt?`, `pendingFirmwareId?`, `pendingFirmwareExpiresAt?`, and `lastFirmwareDownloadedAt?`. It never includes raw WiFi passwords, raw credentials, or generated firmware content.

## Idempotency

Firmware generation is state-guarded by table credential locking: generating a new firmware package rotates the display credential and revokes the previous active credential in the same transaction. One-time firmware download is consume-once. Credential revocation and rotation are state-guarded and audited; no `Idempotency-Key` is required in the current release.
