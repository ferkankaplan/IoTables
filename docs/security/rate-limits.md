# Rate Limit Strategy

This document defines current release rate limit requirements.

It is downstream of:

- [../api/auth.md](../api/auth.md)
- [../api/errors.md](../api/errors.md)
- [../api/idempotency.md](../api/idempotency.md)
- [../modules/access/identity-access.md](../modules/access/identity-access.md)
- [../modules/access/otp-messaging.md](../modules/access/otp-messaging.md)
- [../modules/ordering/table-presence.md](../modules/ordering/table-presence.md)
- [../database/transactions.md](../database/transactions.md)
- [threat-model.md](threat-model.md)

## Principles

- Rate limits reduce abuse and accidental load; they do not replace authorization, idempotency, one-time tokens, database constraints, locks, or transaction boundaries.
- Every limit must be scoped by the narrowest meaningful actor: tenant, user, customer session, table, display credential, IP, route, OTP challenge, or target aggregate.
- Public and unauthenticated limits must avoid tenant/user enumeration.
- Security-sensitive rate limit failures use safe messages and `429 Too Many Requests` with `rate_limit_exceeded`, except OTP verification exhaustion, which may return `otp_locked`.
- V1 defaults must be configuration values. Local development may relax them, but production must not silently disable them.
- If deployment uses more than one backend process, production rate limiting must use a shared store. In-process limits are acceptable only for local development.

## Response Rules

| Response Item | Rule |
| --- | --- |
| HTTP status | `429 Too Many Requests` |
| API code | `rate_limit_exceeded` unless a module-specific code such as `otp_locked` is more precise |
| Headers | `Retry-After` when a retry time is known |
| Body | Standard API error envelope from [../api/errors.md](../api/errors.md) |
| Details | May include safe `retryAfterSeconds`; must not expose whether a hidden user, tenant, OTP target, token, or credential exists |

## Keying Rules

| Surface | Required Key Parts |
| --- | --- |
| Login | normalized app scope + tenant/platform host + username when known + client IP |
| First password setup | tenant/platform host + user/setup token + purpose + client IP |
| OTP challenge/send/verify | tenant + user + purpose + challenge + target GSM hash + client IP where browser-originated |
| QR token redeem | tenant host + client IP + token hash bucket + customer session when present |
| ESP32 QR fetch | tenant + table + display credential hash |
| Customer cart/order | tenant + CustomerOrderingSession + route + client IP |
| Staff mutation | tenant + user + app scope + route + target aggregate where applicable |
| Cashier payment/correction | tenant + cashier user + Check or Payment + route |
| Provisioning | platform owner + route + normalized tenant identity |
| Worker side effects | worker identity + effect type; concurrency cap rather than public rate limit |

When storing rate limit keys, avoid raw secrets. Use normalized identifiers, stable hashes, or HMAC-derived keys where raw values are sensitive.

## Current Release Default Limits

These are initial production defaults. They may be tightened or relaxed through configuration after real operational data exists, but changing them must not weaken module invariants.

### Public and Login

| Action | Scope | Default Limit | Failure |
| --- | --- | --- | --- |
| `identity_access.get_login_requirements` | IP + app scope + host | 60/minute | `rate_limit_exceeded` |
| `identity_access.authenticate` failed attempts | host + username + IP | 5/15 minutes, then progressive backoff | `invalid_credentials` or `rate_limit_exceeded` with generic message |
| `identity_access.authenticate` total attempts | IP + host | 60/minute | `rate_limit_exceeded` |
| `identity_access.change_password` | user session | 10/hour | `rate_limit_exceeded` |
| `identity_access.enroll_totp` | Platform Owner session | 10/hour | `rate_limit_exceeded` |

Login responses must not reveal whether the tenant, username, or role exists.

### First Password and OTP

| Action | Scope | Default Limit | Failure |
| --- | --- | --- | --- |
| Begin first password setup | user + purpose + IP | 5/15 minutes | `rate_limit_exceeded` |
| Create OTP challenge | user + purpose | 5/15 minutes | `rate_limit_exceeded` |
| Send OTP | challenge | Max 3 sends total | `otp_locked` |
| Send OTP cooldown | challenge | 60 seconds between sends | `rate_limit_exceeded` |
| Send OTP to target GSM | tenant + target GSM hash | 10/hour | `rate_limit_exceeded` |
| Verify OTP | challenge | Max 5 attempts total | `otp_locked` |
| Verify OTP burst | challenge + IP | 10/15 minutes | `rate_limit_exceeded` |

OTP limits are enforced in the OTP data model first. Generic request rate limits are an outer abuse shield.

### QR and Table Presence

| Action | Scope | Default Limit | Failure |
| --- | --- | --- | --- |
| ESP32 fetch current QR | display credential | 30/minute | `rate_limit_exceeded` |
| ESP32 fetch current QR burst | display credential | excessive polls return the current live token without creating extra live tokens; successful redemption or expiry may still rotate immediately | `rate_limit_exceeded` only after abusive over-polling |
| Redeem QR token | IP + tenant | 30/minute | `rate_limit_exceeded` |
| Redeem QR token | customer session | 10/minute | `rate_limit_exceeded` |
| Redeem QR token | table | 60/minute | `rate_limit_exceeded` |
| Expired/consumed QR failures | IP + tenant | 20/minute | `rate_limit_exceeded` |

The one-time token remains the primary replay defense. Rate limits must not be the only reason fake orders are prevented.

### Customer Ordering

| Action | Scope | Default Limit | Failure |
| --- | --- | --- | --- |
| Public menu browse | IP + tenant | 120/minute | `rate_limit_exceeded` |
| Presence state read | customer session | 60/minute | `rate_limit_exceeded` |
| Cart read | customer session | 120/minute | `rate_limit_exceeded` |
| Cart mutation | customer session | 60/minute | `rate_limit_exceeded` |
| Order submit | customer session + table | 6/minute | `rate_limit_exceeded` |
| Order submit | table | 60/minute | `rate_limit_exceeded` |
| My Orders / Table Orders | customer session | 60/minute | `rate_limit_exceeded` |
| Customer bill/payment summary | customer session | 60/minute | `rate_limit_exceeded` |

Order submit still requires fresh presence and `Idempotency-Key`; the rate limit only reduces accidental or abusive submission storms.

### Tenant Setup and Platform

| Action | Scope | Default Limit | Failure |
| --- | --- | --- | --- |
| Create tenant | Platform Owner | 10/hour | `rate_limit_exceeded` |
| Retry provisioning | Platform Owner + tenant | 10/hour | `rate_limit_exceeded` |
| Tenant setup write | Tenant Admin session | 60/minute | `rate_limit_exceeded` |
| Table display claim create | Tenant Admin + table | 10/hour | `rate_limit_exceeded` |
| Display credential rotate/revoke | Tenant Admin + table | 10/hour | `rate_limit_exceeded` |
| Staff create/role/scope write | Tenant Admin session | 60/minute | `rate_limit_exceeded` |

Provisioning and starter templates still rely on durable idempotency and one-time application records. Rate limits do not replace no-rerun guarantees.

### Station and Service Staff

| Action | Scope | Default Limit | Failure |
| --- | --- | --- | --- |
| Station queue/workload reads | user + station | 120/minute | `rate_limit_exceeded` |
| Station status mutation | user + station | 120/minute | `rate_limit_exceeded` |
| Service ready/workload reads | user + hall | 120/minute | `rate_limit_exceeded` |
| Single delivery mutation | user + hall | 120/minute | `rate_limit_exceeded` |
| Bulk delivery mutation | user + hall | 30/minute | `rate_limit_exceeded` |

Station and service mutations still require current assignment checks and domain state validation.

### Cashier and Settlement

| Action | Scope | Default Limit | Failure |
| --- | --- | --- | --- |
| Cashier board/session reads | cashier + tenant | 120/minute | `rate_limit_exceeded` |
| Bill/check/payment reads | cashier + Check | 120/minute | `rate_limit_exceeded` |
| Record payment | cashier + Check | 30/minute | `rate_limit_exceeded` |
| Void payment | cashier + Payment | 10/minute | `rate_limit_exceeded` |
| Record cashier correction | cashier + Check | 10/minute | `rate_limit_exceeded` |
| Close session | cashier + TableSession | 10/minute | `rate_limit_exceeded` |

Payment, void, correction, and close flows remain protected by role checks, idempotency, Check/TableSession locks, and domain rules.

### Governance, Audit, and Side Effects

| Action | Scope | Default Limit | Failure |
| --- | --- | --- | --- |
| Audit query | authorized user + tenant/platform scope | 60/minute | `rate_limit_exceeded` |
| Failed side-effect list | Platform/recovery user | 60/minute | `rate_limit_exceeded` |
| Outbox worker claim | worker identity + effect type | concurrency cap, not public rate limit | internal backoff |
| Outbox stale claim recovery | worker/recovery identity | concurrency cap, not public rate limit | internal backoff |

Worker rate control is about concurrency and provider backoff. It must not cause permanent side-effect loss.

## Lockout and Cooldown Rules

- Temporary rate limits must expire automatically.
- Security lockouts that change domain state, such as OTP lock, must be represented in the owning module's data model.
- Login throttling should use progressive delay before hard lockout to avoid easy denial-of-service against known usernames.
- Platform Owner and Tenant Admin lockout recovery must require explicit recovery tooling; do not create automatic bypasses.

## Observability

Every rate limit decision should produce safe telemetry:

| Field | Rule |
| --- | --- |
| `requestId` | Required for correlation |
| `tenantId` | Allowed when known and safe |
| `route` / command | Allowed |
| `limitKeyHash` | Allowed; do not log raw token, OTP, credential, or session |
| `decision` | allowed / limited / locked |
| `retryAfterSeconds` | Allowed |
| Raw IP | Avoid in app logs when a hashed/network-safe representation is enough |

Rate limit events are product/security telemetry. They are not a substitute for audit events required by module contracts.

## Verification Requirements

| Area | Required Test |
| --- | --- |
| Login | Failed login throttles without user enumeration. |
| OTP | Send cooldown, max sends, max verify attempts, and target GSM rate limits work together. |
| QR | Token replay still fails when rate limiter is disabled; limiter blocks redeem storms. |
| Customer order submit | Duplicate submit remains idempotent under and over the limit. |
| Cashier payment | Repeated clicks return idempotent result or rate limit without duplicate Payment. |
| Tenant isolation | Rate limit keys do not let one tenant affect another tenant's normal traffic except shared IP abuse limits. |
| Outbox | Worker concurrency cap does not drop claimed work and stale claim recovery still runs. |

## Open Questions

None currently.
