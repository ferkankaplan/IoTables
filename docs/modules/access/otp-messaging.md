# Module: OTP / Messaging

## Purpose

OTP / Messaging owns one-time password creation, delivery, verification, expiry, retry, and provider integration.

It supports sensitive first-login password setup flows for tenant admin and cashier.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| OTP challenge | Entity | create, expire, verify |
| OTP delivery | Side effect | send through provider |
| OTP verification attempt | Audit/security record | record attempts and failures |
| Messaging provider integration | External adapter | send and handle provider errors |

## Not Owned

- User credentials.
- Tenant GSM source of truth.
- Staff role decisions.
- Payment provider calls.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| TenantApp / Tenant Admin | request/verify first setup OTP | Own tenant |
| CashierApp / Cashier | request/verify first setup OTP | Sent to tenant GSM during bootstrap |
| PlatformApp | trigger provisioning flows that require OTP later | Cannot bypass verification |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Create OTP challenge | Start verification | Identity and Access |
| Send OTP | Deliver code to GSM | Identity and Access |
| Verify OTP | Complete sensitive flow | Identity and Access |
| Get challenge state | Show retry/expiry UX | TenantApp, CashierApp |

## Internal Rules

- OTPs are short-lived.
- OTP values must be stored hashed or otherwise non-recoverable.
- OTP verification is required for tenant admin first password setup.
- OTP verification is required for cashier first password setup and is sent to tenant GSM in v1.
- Station and service staff do not require OTP in v1.
- OTP retries must be rate-limited.
- V1 OTP lifetime is 5 minutes.
- V1 allows at most 5 verification attempts per challenge.
- V1 allows at most 3 send attempts per challenge with cooldown between sends.
- Concrete SMS provider selection is an adapter/configuration decision, not an app/module contract. The module depends on a provider interface and records delivery attempts regardless of provider.

## Operational Safety

- Sending SMS is not transactionally rollbackable; flows must tolerate delivery failures.
- OTP verification must be idempotent after success.
- Repeated failed attempts must lock or slow the challenge.
- Provider errors must be recorded and surfaced safely.
- OTP codes must never be logged in plaintext.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| OtpChallenge | Verification lifecycle | target GSM, purpose, expiresAt, verifiedAt |
| OtpAttempt | Attempt tracking | rate limits and audit |
| MessageDelivery | Provider delivery record | provider id/status/error |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Tenant admin first password setup |
| CashierApp | Cashier first password setup |

## Future Service Boundary

- Own data: OTP challenges, attempts, delivery records.
- Own APIs: create challenge, send, verify, status.
- Published events: otp.verified, otp.failed, message.sent.
- Consumed events: user.first_login_required.
- Must not leak: OTP code, provider secrets.

## Open Questions

None currently.
