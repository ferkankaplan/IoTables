# API Contracts: OTP Messaging

Source contracts: [otp-messaging-contracts.md](otp-messaging-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

OTP Messaging owns challenge state, SMS delivery attempts, verification, send limits, and attempt limits. It never exposes OTP codes.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/auth/otp-challenges/{challengeId}` | TenantApp, CashierApp | `otp_messaging.get_challenge_state` | Matching setup flow/session | Path: `challengeId` | `OtpChallengeState` | `not_authorized`, `otp_expired`, `otp_locked` |
| `POST` | `/api/auth/otp-challenges/{challengeId}/send` | TenantApp, CashierApp | `otp_messaging.send_otp` | Matching setup flow/session + CSRF | none | `OtpDeliveryState` | `otp_expired`, `otp_locked`, `delivery_failed` |
| `POST` | `/api/auth/otp-challenges/{challengeId}/verify` | TenantApp, CashierApp | `otp_messaging.verify_otp` | Matching setup flow/session + CSRF | Body: `code` | `OtpVerificationResult` | `otp_invalid`, `otp_expired`, `otp_locked` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `otp_messaging.create_challenge` | Called by Identity and Access when first-password setup requires OTP. |
| `otp_messaging.expire_or_lock_challenge` | Internal policy action/job only. |
| `otp_messaging.get_delivery_state` | Recovery/support tooling only; no normal app endpoint in the current release. |

## Request Schemas

`OtpVerifyRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `code` | string | yes | User-submitted OTP. Never logged. |

## Response Schemas

`OtpChallengeState`:

| Field | Type | Notes |
| --- | --- | --- |
| `challengeId` | string | Challenge identifier. |
| `purpose` | string enum | Example: first-password setup. |
| `targetHint` | string | Masked GSM display only. |
| `expiresAt` | timestamp | UTC. |
| `remainingAttempts` | integer | Does not reveal code. |
| `remainingSends` | integer | Current release max sends enforced. |
| `verified` | boolean | True after successful verification. |

`OtpDeliveryState` includes `challengeId`, `sendCount`, `lastDeliveryStatus`, and `nextSendAllowedAt`.

`OtpVerificationResult` includes `challengeId`, `verified`, and `proofToken` when verification succeeds. The proof token is consumed by Identity and Access and must not be reusable after setup completion.

## Idempotency

OTP verification is guarded by locked challenge state and idempotent success semantics. It does not require `Idempotency-Key`.
