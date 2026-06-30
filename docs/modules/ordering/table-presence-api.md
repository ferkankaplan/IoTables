# API Contracts: Table Presence

Source contracts: [table-presence-contracts.md](table-presence-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Table Presence owns short-lived QR token issuance, one-time redemption, and fresh physical table presence.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/table-display/qr-token` | ESP32 display | `table_presence.issue_current_qr_token` | `Authorization: DisplayCredential ...` | none | `QrTokenPayload` | `display_not_authenticated`, `credential_revoked`, `wrong_table_or_tenant` |
| `POST` | `/api/v1/customer/table-presence/redeem` | CustomerApp | `table_presence.redeem_token` | Raw QR token + optional customer session cookie | Body: `qrToken` | `PresenceRedeemResult` | `token_expired`, `token_consumed`, `tenant_unavailable` |
| `GET` | `/api/v1/customer/table-presence` | CustomerApp | `table_presence.get_presence_state` | Customer session cookie | none | `PresenceState` | `session_expired`, `fresh_presence_required` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `table_presence.require_fresh_presence` | Server-side guard used by order submit and customer-visible table/session reads. |
| `table_presence.expire_old_tokens` | Internal retention job only. |

## Request Schemas

`PresenceRedeemRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `qrToken` | string | yes | Raw one-time token from QR. Never logged raw. |

## Response Schemas

`QrTokenPayload`:

| Field | Type | Notes |
| --- | --- | --- |
| `qrToken` | string | Raw token encoded into QR. |
| `expiresAt` | timestamp | Token expiry. |
| `refreshAfterSeconds` | integer | ESP32 display refresh hint. |

`PresenceRedeemResult`:

| Field | Type | Notes |
| --- | --- | --- |
| `customerOrderingSessionId` | string | Anonymous browser ordering session. |
| `tableId` | string | Trusted server-resolved table. |
| `hallId` | string | Trusted server-resolved hall. |
| `freshUntil` | timestamp | Presence window expiry. |
| `cartPreserved` | boolean | True when compatible existing customer session was refreshed. |

`PresenceState` includes `customerOrderingSessionId`, `tableId`, `hallId`, `freshUntil`, and `fresh`.

## Cookie Behavior

Successful QR redemption sets or refreshes the CustomerOrderingSession Secure, HttpOnly cookie. The raw cookie token is not returned in JSON.

## Idempotency

QR redemption does not use `Idempotency-Key`. The QR token is a one-time secret consumed atomically. Reusing the same token returns `410 token_consumed` or an equivalent terminal error.
