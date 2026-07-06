# API Contracts: OTP Messaging

Source contracts: [otp-messaging-contracts.md](otp-messaging-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

OTP Messaging owns challenge state, SMS delivery attempts, verification, send limits, and attempt limits. It never exposes OTP codes.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/api/platform/tenant-creation-otp/begin` | PlatformApp | `otp_messaging.create_challenge` | Platform Owner session + CSRF | Body: `gsmNumber` | `TenantCreationOtpBeginResponse` | `otp_locked`, `validation_failed` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `otp_messaging.create_challenge` | Called by PlatformApp tenant creation and future password reset flows. |
| `otp_messaging.verify_otp` | Called by PlatformApp tenant creation and future password reset flows. |
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
| `purpose` | string enum | Example: tenant creation or password reset. |
| `targetHint` | string | Masked GSM display only. |
| `expiresAt` | timestamp | UTC. |
| `remainingAttempts` | integer | Does not reveal code. |
| `remainingSends` | integer | Current release max sends enforced. |
| `verified` | boolean | True after successful verification. |

`OtpDeliveryState` includes `challengeId`, `sendCount`, `lastDeliveryStatus`, and `nextSendAllowedAt`.

`OtpVerificationResult` includes `challengeId`, `verified`, and `proofToken` when verification succeeds. The proof token is consumed by Identity and Access and must not be reusable after setup completion.

## Idempotency

OTP verification is guarded by locked challenge state and idempotent success semantics. It does not require `Idempotency-Key`.
