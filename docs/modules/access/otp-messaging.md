# Module: OTP / Messaging

## Purpose

OTP / Messaging owns one-time password creation, delivery, verification, expiry, retry, and provider integration.

It supports sensitive tenant creation and password reset verification flows.

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
| PlatformApp / Platform Owner | request/verify tenant creation OTP | Sent to the tenant identity GSM before Provisioning starts |
| TenantApp / Tenant Admin | request/verify first-password and password reset OTP | Own tenant; target is platform-owned tenant identity GSM |
| CashierApp / Cashier | request/verify first-password and password reset OTP | Own tenant; target is platform-owned tenant identity GSM |
| StationStaffApp / Station Staff | request/verify first-password OTP | Own tenant; target is platform-owned tenant identity GSM |
| ServiceStaffApp / Service Staff | request/verify first-password OTP | Own tenant; target is platform-owned tenant identity GSM |

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
- OTP verification is required before PlatformApp creates a tenant.
- OTP verification is required for staff password reset flows.
- First password setup requires OTP sent to the platform-owned tenant identity GSM; temporary starter passwords must still be changed on first login.
- Staff password reset OTP is sent to the platform-owned tenant identity GSM number, which only PlatformApp may change.
- OTP retries must be rate-limited.
- Current release OTP lifetime is 5 minutes.
- The current release allows at most 5 verification attempts per tenant/challenge.
- The current release allows at most 3 send attempts per tenant/challenge with cooldown between sends.
- Concrete SMS provider selection is an adapter/configuration decision, not an app/module contract. The module depends on a provider interface and records delivery attempts regardless of provider.

## Operational Safety

- Sending SMS is not transactionally rollbackable; flows must tolerate delivery failures.
- OTP verification must be idempotent after success.
- Repeated failed attempts must lock or slow the challenge.
- Provider errors must be recorded and surfaced safely.
- OTP codes must never be logged in plaintext.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| OtpChallenge | created -> sent -> verified / expired / locked | tenant when tenant-scoped, user when user-scoped, purpose, targetGsm, codeHash, expiresAt, verifiedAt | Code stored hashed/non-recoverable; 5 minute lifetime in the current release; verification idempotent after success; platform-scoped tenant creation challenges have no tenant; existing challenge target must not silently change if tenant GSM changes | Retain safe challenge metadata for audit/rate-limit review; never retain plaintext code |
| OtpAttempt | recorded per verification attempt | tenant when tenant-scoped, challenge, attemptNo, result, createdAt | At most 5 verification attempts per challenge in the current release; attempt numbers unique per challenge | Append-only security record |
| MessageDelivery | queued -> sent / failed | tenant when tenant-scoped, challenge, deliveryNo, provider, providerMessageRef, status, redacted errorSummary | At most 3 send attempts per challenge in the current release; provider response must not store OTP code/secrets/raw sensitive payload | Preserve attempts for troubleshooting and abuse review according to retention policy |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Tenant creation GSM verification |
| TenantApp | Staff password reset flows for tenant staff |
| CashierApp | Cashier password reset flow |

## Future Service Boundary

- Own data: OTP challenges, attempts, delivery records.
- Own APIs: create challenge, send, verify, status.
- Published events: otp.verified, otp.failed, message.sent.
- Consumed events: user.first_login_required.
- Must not leak: OTP code, provider secrets.

## Open Questions

None currently.
