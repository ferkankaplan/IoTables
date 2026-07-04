# API Contracts: Identity and Access

Source contracts: [identity-access-contracts.md](identity-access-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Identity and Access owns human login sessions, credentials, first-password setup, reserved future Platform Owner TOTP support, and user disablement.

CustomerApp does not use these endpoints.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/auth/login-requirements` | Login surfaces | `identity_access.get_login_requirements` | Public safe read | Query: `appScope`, `username` | `LoginRequirements` | `tenant_unavailable` |
| `POST` | `/api/v1/auth/login` | PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp | `identity_access.authenticate` | Public + CSRF if browser form uses cookie preflight | Body: `LoginRequest` | `LoginResult` | `invalid_credentials`, `first_password_change_required`, `otp_required`, `wrong_app_scope` |
| `POST` | `/api/v1/auth/first-password/begin` | TenantApp, CashierApp, staff apps | `identity_access.begin_first_password_setup` | Setup token | Body: `setupToken` | `FirstPasswordSetupState` | `invalid_credentials`, `otp_required`, `setup_token_invalid` |
| `POST` | `/api/v1/auth/first-password/complete` | TenantApp, CashierApp, staff apps | `identity_access.complete_first_password_setup` | Setup token + OTP proof when required | Body: `CompleteFirstPasswordRequest` | `LoginResult` or `CredentialSetupResult` | `otp_required`, `otp_invalid`, `password_policy_failed` |
| `POST` | `/api/v1/auth/change-password` | Authenticated human apps | `identity_access.change_password` | App session + CSRF | Body: `currentPassword`, `newPassword` | `PasswordChangedResult` | `invalid_credentials`, `password_policy_failed` |
| `POST` | `/api/v1/auth/totp/enroll` | PlatformApp | `identity_access.enroll_totp` | Reserved for future PlatformApp hardening; not required by v1 login | Body: `TotpEnrollRequest` | `LoginResult` | `totp_invalid`, `invalid_credentials`, `totp_already_enrolled` |
| `POST` | `/api/v1/auth/logout` | Authenticated human apps | `identity_access.logout_or_revoke_session` | App session + CSRF | Body optional: `sessionId` for own session | `LogoutResult` | `not_authorized` |
| `GET` | `/api/v1/auth/session` | Authenticated human apps | `identity_access.validate_session` | App session | none | `AuthenticatedActor` | `session_expired`, `wrong_app_scope` |
| `GET` | `/api/v1/tenant/users/{userId}` | TenantApp | `identity_access.get_user` | Tenant Admin session | Path: `userId` | `UserProfile` | `not_authorized`, `not_found_or_hidden` |
| `POST` | `/api/v1/tenant/users/{userId}/disable` | TenantApp | `identity_access.disable_user` | Tenant Admin session + CSRF | Body: `reason` | `UserProfile` | `not_authorized`, `reason_required`, `last_admin_not_allowed` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `identity_access.create_platform_owner` | No normal app endpoint. Explicit bootstrap tooling only. |
| `identity_access.create_bootstrap_user` | No direct generic endpoint in v1. Exposed through staff management and provisioning flows. |
| `identity_access.require_app_scope` | Gateway/module guard only. |

## Request Schemas

`LoginRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `appScope` | string enum | yes | One of PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp. |
| `username` | string | yes | Tenant users are scoped by host tenant. |
| `password` | string | yes | Never logged. |
| `totpCode` | string | no | Reserved for future PlatformApp hardening; ignored by v1 PlatformApp login. |

Tenant-scoped login resolves tenant context from the request host in production. Local development and automated tests may pass `X-Tenant-Subdomain` as an explicit tenant context fallback; production clients must not rely on body/query `tenantId`.

In v1, valid Platform Owner username/password creates a PlatformApp session directly. Login does not return `totp_enrollment_required` or `totp_required` for PlatformApp.

`TotpEnrollRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `username` | string | yes | Platform Owner username. |
| `password` | string | yes | Password proof for first TOTP setup. |
| `secret` | string | yes | Server-generated setup secret from `LoginResult.totpSetup`. |
| `totpCode` | string | yes | Current authenticator code proving the secret was enrolled. |

`CompleteFirstPasswordRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `setupToken` | string | yes | One-time setup context. |
| `newPassword` | string | yes | Validated by password policy. |
| `otpChallengeId` | string | conditional | Required for tenant admin and cashier. |
| `otpCode` | string | conditional | Required for tenant admin and cashier. |

## Response Schemas

`FirstPasswordSetupState`:

| Field | Type | Notes |
| --- | --- | --- |
| `status` | string enum | `otp_required` when OTP proof is required before completion. |
| `setupToken` | string | Existing setup token; no authenticated app session exists yet. |
| `otpRequired` | boolean | True for Tenant Admin and Cashier first-password setup in v1. |
| `otpChallengeId` | string/null | Challenge identifier to submit during completion. |
| `targetHint` | string/null | Masked tenant GSM display only. |
| `expiresAt` | timestamp/null | OTP challenge expiry. |
| `remainingAttempts` | integer/null | Remaining verification attempts; does not reveal the code. |

The OTP code is never returned, logged, or stored in recoverable form. `/api/v1/auth/first-password/begin` creates the OTP challenge and records a redacted SMS delivery attempt; actual provider delivery is handled as a side effect. Repeated begin calls with the same still-valid setup context return the active unverified challenge state instead of creating duplicate OTP challenges.

`LoginResult`:

| Field | Type | Notes |
| --- | --- | --- |
| `status` | string enum | `authenticated`, `first_password_required`, `otp_required`. |
| `actor` | `AuthenticatedActor`/null | Present after successful authentication. |
| `setupToken` | string/null | Returned only for first-password setup. |
| `expiresAt` | timestamp/null | Login session expiry when authenticated. |
| `totpSetup` | object/null | Reserved for future PlatformApp hardening; null in v1 PlatformApp login. |

`AuthenticatedActor` includes `userId`, `tenantId?`, `appScope`, `roles`, `stationIds`, `hallIds`, and safe display fields.

## Cookie Behavior

Successful login sets a Secure, HttpOnly, SameSite cookie scoped for the app/host. The response body must not include raw session tokens.

## Idempotency

Login, logout, password change, and first-password setup do not require `Idempotency-Key`. They rely on credential/session state, setup tokens, OTP challenge guards, and audit records.
