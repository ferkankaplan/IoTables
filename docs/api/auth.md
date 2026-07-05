# API Authentication and Session Standards

This document defines shared authentication and request authorization rules for API endpoints.

The permission source is [../modules/access/permission-policy-matrix.md](../modules/access/permission-policy-matrix.md). This document only defines how API requests carry identity/session evidence.

## Session Types

| Session Type | Actor | Transport | Owner |
| --- | --- | --- | --- |
| Platform session | Platform Owner | Secure HttpOnly host cookie on the platform host, such as `platform.iotables.net` or `platform.tabflow.uk` | Identity and Access |
| Tenant staff/admin session | Tenant Admin, Cashier, Station Staff, Service Staff | Secure HttpOnly host cookie on the tenant host, such as `[tenant].iotables.net` or `[tenant].tabflow.uk` | Identity and Access |
| Customer ordering session | Anonymous Customer | Secure HttpOnly host cookie on the tenant host, such as `[tenant].iotables.net` or `[tenant].tabflow.uk` | Customer Ordering |
| Table display credential | ESP32 table display | Dedicated display credential auth header | Table Display Provisioning |
| Worker identity | Background worker | Internal configuration/runtime identity | Reliable Side Effects |

Frontend JavaScript must not receive raw human session tokens, customer cookie token secrets, OTP codes, password hashes, display credentials, or QR token hashes.

## Cookie Rules

Human and customer browser sessions use cookies with:

| Attribute | Rule |
| --- | --- |
| `HttpOnly` | Required. |
| `Secure` | Required outside local development. |
| `SameSite` | `Lax` default in the current release. |
| `Path` | API/app appropriate path; avoid broader scope than needed. |
| Domain | Host-only where possible; do not share PlatformApp cookies with tenant subdomains. |

Tenant subdomains must not be able to read or overwrite PlatformApp session cookies.

## CSRF

All unsafe cookie-auth requests require CSRF protection.

Unsafe methods:

- `POST`
- `PATCH`
- `PUT`
- `DELETE`

Required header:

```text
X-CSRF-Token: <csrf-token>
```

Rules:

- CSRF tokens must be bound to the session.
- Missing/invalid CSRF token returns `csrf_failed`.
- CustomerApp commands such as cart mutation and order submit require CSRF when cookie-authenticated.
- ESP32 display credential requests do not use browser cookies and do not use CSRF.

## Human App Authentication

Human app requests must pass:

1. tenant/platform host resolution;
2. session cookie validation;
3. app scope validation;
4. role/scope validation where required;
5. domain state validation.

Platform Owner:

- `tenant_id = null`;
- PlatformApp scope only;
- username/password login only in the current release.

Tenant users:

- session tenant must match request tenant subdomain;
- app scope must match requested app surface;
- role and station/hall scope are checked by Staff Access.

## First Password Setup

Bootstrap users cannot enter normal app workflows until first password setup completes.

| User | OTP Requirement |
| --- | --- |
| Platform Owner | No OTP/TOTP requirement in the current release |
| Tenant Admin | OTP SMS to tenant GSM required |
| Cashier | OTP SMS to tenant GSM required |
| Station Staff | OTP not required in the current release |
| Service Staff | OTP not required in the current release |

OTP challenges are created when first password setup begins, not during tenant provisioning.

## CustomerApp Authentication

CustomerApp does not use Identity and Access.

Customer protected requests require:

- tenant active;
- CustomerOrderingSession cookie;
- table/session compatibility where relevant;
- fresh QR presence for order submit, table orders, bill summary, and balance visibility.

CustomerApp may browse public menu data without a customer session, but order submission and table-specific visibility require the session/presence rules above.

## ESP32 Display Authentication

The ESP32 table display is not a user.

Use a dedicated display credential header for QR fetch requests:

```text
Authorization: DisplayCredential <credential-secret>
```

Rules:

- The backend stores only the credential hash.
- The backend resolves tenant/table from the credential.
- ESP32 requests must not supply trusted tenant/table IDs.
- Revoked credentials fail closed.
- Display credentials must never appear in QR payloads.

## Internal Worker Authentication

Workers are not public API clients.

Rules:

- Workers may only claim and process reliable side effects.
- Worker identity must not bypass module command guards for business mutation.
- Provider responses must be redacted before storage.

## CORS

Production API calls should be same-origin for the active app host.

Development may allow explicit localhost origins for Vite/FastAPI. Wildcard credentialed CORS is forbidden.

## Failure Codes

| Failure | Meaning |
| --- | --- |
| `unauthenticated` | No valid session/credential was provided. |
| `session_expired` | Session exists but is expired or revoked. |
| `csrf_failed` | Unsafe cookie-auth request failed CSRF validation. |
| `wrong_app_scope` | Session exists but cannot access this app/API surface. |
| `not_authorized` | Actor lacks required role or permission. |
| `wrong_scope` | Actor lacks required tenant/station/hall/table scope. |
