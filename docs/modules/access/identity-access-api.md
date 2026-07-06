# API Contracts: Identity and Access

Source contracts: [identity-access-contracts.md](identity-access-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Identity and Access owns human login sessions, credentials, first-password setup, reserved future Platform Owner TOTP support, and user disablement.

CustomerApp does not use these endpoints.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/auth/login-requirements` | Login surfaces | `identity_access.get_login_requirements` | Public safe read | Query: `appScope`, `username` | `LoginRequirements` | `tenant_unavailable` |
| `POST` | `/api/auth/login` | PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp | `identity_access.authenticate` | Public + CSRF if browser form uses cookie preflight | Body: `LoginRequest` | `LoginResult` | `invalid_credentials`, `first_password_change_required`, `wrong_app_scope` |
| `POST` | `/api/auth/first-password/begin` | TenantApp, CashierApp, staff apps | `identity_access.begin_first_password_setup` | Setup token | Body: `setupToken` | `FirstPasswordSetupState` | `invalid_credentials`, `setup_token_invalid` |
| `POST` | `/api/auth/first-password/complete` | TenantApp, CashierApp, staff apps | `identity_access.complete_first_password_setup` | Setup token | Body: `CompleteFirstPasswordRequest` | `LoginResult` or `CredentialSetupResult` | `password_policy_failed` |
| `POST` | `/api/auth/change-password` | Authenticated human apps | `identity_access.change_password` | App session + CSRF | Body: `currentPassword`, `newPassword` | `PasswordChangedResult` | `invalid_credentials`, `password_policy_failed` |
| `POST` | `/api/auth/totp/enroll` | PlatformApp | `identity_access.enroll_totp` | Reserved for future PlatformApp hardening; not required by current release login | Body: `TotpEnrollRequest` | `LoginResult` | `totp_invalid`, `invalid_credentials`, `totp_already_enrolled` |
| `POST` | `/api/auth/logout` | Authenticated human apps | `identity_access.logout_or_revoke_session` | App session + CSRF | Body optional: `sessionId` for own session | `LogoutResult` | `not_authorized` |
| `GET` | `/api/auth/session` | Authenticated human apps | `identity_access.validate_session` | App session | none | `AuthenticatedActor` | `session_expired`, `wrong_app_scope` |
| `GET` | `/api/tenant/users/{userId}` | TenantApp | `identity_access.get_user` | Tenant Admin session | Path: `userId` | `UserProfile` | `not_authorized`, `not_found_or_hidden` |
| `POST` | `/api/tenant/users/{userId}/disable` | TenantApp | `identity_access.disable_user` | Tenant Admin session + CSRF | Body: `reason` | `UserProfile` | `not_authorized`, `reason_required`, `last_admin_not_allowed` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `identity_access.create_platform_owner` | No normal app endpoint. Explicit bootstrap tooling only. |
| `identity_access.create_bootstrap_user` | No direct generic endpoint in the current release. Exposed through staff management and provisioning flows. |
| `identity_access.require_app_scope` | Gateway/module guard only. |

## Request Schemas

`LoginRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `appScope` | string enum | yes | One of PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp. |
| `username` | string | yes | Tenant users are scoped by host tenant. |
| `password` | string | yes | Never logged. |
| `totpCode` | string | no | Reserved for future PlatformApp hardening; ignored by current release PlatformApp login. |

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
| `status` | string enum | `password_change_required` in the current release. |
| `setupToken` | string | Existing setup token; no authenticated app session exists yet. |
| `otpRequired` | boolean | False for all current release first-password setup flows. |
| `otpChallengeId` | string/null | Null for current release first-password setup. |
| `targetHint` | string/null | Null for current release first-password setup. |
| `expiresAt` | timestamp/null | Null for current release first-password setup. |
| `remainingAttempts` | integer/null | Null for current release first-password setup. |

The OTP code is never returned, logged, or stored in recoverable form. Current release first-password setup does not create OTP challenges. OTP challenge creation is used by tenant creation and password reset flows.

`LoginResult`:

| Field | Type | Notes |
| --- | --- | --- |
| `status` | string enum | `authenticated`, `first_password_required`. |
| `actor` | `AuthenticatedActor`/null | Present after successful authentication. |
| `setupToken` | string/null | Returned only for first-password setup. |
| `expiresAt` | timestamp/null | Login session expiry when authenticated. |
| `totpSetup` | object/null | Reserved for future PlatformApp hardening; null in the current release PlatformApp login. |

`AuthenticatedActor` includes `userId`, `tenantId?`, `appScope`, `roles`, `stationIds`, `hallIds`, and safe display fields.

## Cookie Behavior

Successful login sets a Secure, HttpOnly, SameSite cookie scoped for the app/host. The response body must not include raw session tokens.

## Idempotency

Login, logout, password change, and first-password setup do not require `Idempotency-Key`. They rely on credential/session state, setup tokens, and audit records.
