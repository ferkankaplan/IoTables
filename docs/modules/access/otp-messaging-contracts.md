# Module Contracts: OTP Messaging

Source module: [otp-messaging.md](otp-messaging.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `otp_messaging.create_challenge` | PlatformApp, Identity and Access | tenantId?, userId, purpose, targetGsm | Purpose supported; target GSM snapshotted; tenant creation uses platform user with `tenantId = null`; password reset users belong to tenant | Create challenge with hashed code and expiry; do not retarget existing challenge | OTP challenge state |
| `otp_messaging.send_otp` | PlatformApp, Identity and Access, worker | challengeId | Challenge not expired/verified/locked; tenant creation/password reset flow owns challenge; max 3 sends in the current release; provider payload redacted | Insert `message_deliveries`; enqueue Reliable Side Effects outbox work; provider send happens only after commit | Delivery attempt state |
| `otp_messaging.verify_otp` | PlatformApp, Identity and Access | challengeId, submitted code | Challenge active; target GSM must match the protected command; max 5 attempts; code compared against hash | Lock challenge; append attempt; verification idempotent after success | Verified proof or failure state |
| `otp_messaging.expire_or_lock_challenge` | OTP Messaging | challengeId, reason | Internal policy action | Mark effective terminal state through challenge/attempt metadata | Expired/locked state |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `otp_messaging.get_challenge_state` | PlatformApp, TenantApp, CashierApp, Identity and Access | challengeId | User/session must match tenant creation or password reset flow; do not expose OTP code | Expiry, retry count, send count, verification state |
| `otp_messaging.get_delivery_state` | Identity and Access, support/recovery | challengeId | Tenant/admin scope | Redacted delivery attempts |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `otp.verified` | OTP verification succeeds | Identity and Access, Audit |
| `otp.delivery_failed` | SMS provider fails after attempt | Identity setup UX, recovery tooling |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `otp_expired` | Challenge lifetime ended. |
| `otp_locked` | Attempt or send limit exceeded. |
| `otp_invalid` | Submitted code did not verify. |
| `delivery_failed` | Provider failed or timed out with redacted result. |
| `target_changed_not_applied` | Tenant identity GSM changed after challenge creation; existing challenge still uses original target. |
