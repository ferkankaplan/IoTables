# API Contracts: Table Display Provisioning

Source contracts: [table-display-provisioning-contracts.md](table-display-provisioning-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Table Display Provisioning owns ESP32 claim exchange, display credentials, credential revocation, and display status. The device is a table display surface only.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/api/tenant-setup/tables/{tableId}/display-claims` | TenantApp | `table_display.create_claim` | Tenant Admin session + CSRF | Path: `tableId` | `DisplayClaimCreated` | `not_authorized`, `not_found_or_hidden` |
| `POST` | `/api/table-displays/claims/consume` | ESP32 setup flow | `table_display.consume_claim` | Raw claim secret | Body: `claimSecret` | `DisplayCredentialIssued` | `claim_expired`, `claim_consumed` |
| `GET` | `/api/tenant-setup/tables/{tableId}/display-state` | TenantApp | `table_display.get_display_state` | Tenant Admin session | Path: `tableId` | `DisplayState` | `not_authorized`, `not_found_or_hidden` |
| `POST` | `/api/tenant-setup/tables/{tableId}/display-credential/revoke` | TenantApp | `table_display.revoke_credential` | Tenant Admin session + CSRF | Body: `reason` | `DisplayState` | `reason_required`, `not_found_or_hidden` |
| `POST` | `/api/tenant-setup/tables/{tableId}/display-credential/rotate` | TenantApp | `table_display.rotate_credential` | Tenant Admin session + CSRF | Body: `reason` | `DisplayCredentialIssued` | `reason_required`, `not_found_or_hidden` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `table_display.authenticate_credential` | Used as the authentication guard for QR fetch endpoints in Table Presence. |

## Request Schemas

`DisplayClaimConsumeRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `claimSecret` | string | yes | One-time secret shown/entered during ESP32 provisioning. Never logged. |

## Response Schemas

`DisplayClaimCreated`:

| Field | Type | Notes |
| --- | --- | --- |
| `claimId` | string | Claim identifier. |
| `claimSecret` | string | Returned once. Never persisted raw. |
| `expiresAt` | timestamp | Short-lived. |

`DisplayCredentialIssued`:

| Field | Type | Notes |
| --- | --- | --- |
| `credentialId` | string | Credential identifier. |
| `credentialSecret` | string | Returned once to ESP32. Never persisted raw. |
| `tableId` | string | Bound table. |
| `issuedAt` | timestamp | UTC. |

`DisplayState` includes `tableId`, `activeCredentialId?`, `credentialStatus`, `lastIssuedAt?`, `lastRevokedAt?`, `pendingClaimId?`, and `pendingClaimExpiresAt?`. It never includes raw secrets.

## Idempotency

Claim consumption is guarded by atomic one-time consume. Credential revocation and rotation are state-guarded and audited; no `Idempotency-Key` is required in the current release.
