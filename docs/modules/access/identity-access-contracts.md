# Module Contracts: Identity and Access

Source module: [identity-access.md](identity-access.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `identity_access.create_platform_owner` | Bootstrap tool | username, initial credential material | Explicit bootstrap only; no active Platform Owner exists; no app startup seed | Unique active Platform Owner; create user, credential, platform role, audit | Platform Owner user |
| `identity_access.create_bootstrap_user` | Provisioning, TenantApp | tenantId, username, role intent, temporary credential flag | Caller authorized by Provisioning or Tenant Admin; username unique in tenant/platform scope | Insert user and credential in caller transaction where possible | User with first password change required |
| `identity_access.authenticate` | PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp | tenant/app scope, username, password | Tenant/app scope must match user; disabled users fail; bootstrap users may be forced into setup flow | Create `login_sessions` only after required factors pass | Login session or first-login requirement |
| `identity_access.begin_first_password_setup` | TenantApp, CashierApp, staff apps | userId/setup token | Bootstrap credential required; tenant admin and cashier require OTP; station/service staff do not | Create/send OTP challenge when required; otherwise return password setup state | Setup state and OTP challenge state when required |
| `identity_access.complete_first_password_setup` | TenantApp, CashierApp, staff apps | userId/session setup token, new password, OTP proof when required | Bootstrap credential required; OTP required for tenant admin and cashier only; password policy | Lock user credential; replace password hash; clear bootstrap flag; audit | Active credential and app-appropriate login state |
| `identity_access.change_password` | Authenticated user | current password, new password | Active user; current password valid | Lock credential; update password hash; audit | Password changed |
| `identity_access.enroll_totp` | PlatformApp | platform owner user, TOTP secret proof | Reserved for future PlatformApp hardening; not required before dashboard access in v1 | Store encrypted TOTP secret; audit | Enabled TOTP factor |
| `identity_access.logout_or_revoke_session` | Any authenticated app, admin recovery | sessionId or userId/session filter | User owns session or admin recovery is authorized | Set `revoked_at`; no deletion of session metadata | Revoked session |
| `identity_access.disable_user` | TenantApp, Platform recovery | userId, reason | Tenant Admin own tenant or Platform recovery; cannot disable only active Platform Owner without replacement/recovery rule | Lock user; set disabled; revoke sessions; audit | Disabled user |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `identity_access.get_login_requirements` | Login surfaces | tenant/app scope, username | Do not expose whether hidden tenant/user exists beyond safe login response | Password/first-password/OTP requirement state |
| `identity_access.validate_session` | All authenticated apps | session token | Token hash exists, not expired/revoked, user active, app/tenant scope matches | Authenticated actor context |
| `identity_access.require_app_scope` | Modules and app gateways | actor, required app scope | Server-side only; frontend visibility not trusted | Success or not_authorized |
| `identity_access.get_user` | TenantApp, modules | tenantId/userId | Tenant scoped unless platform user | Safe user profile/status |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `otp_messaging.create_challenge` | Create first-password OTP challenge for tenant admin/cashier. |
| `otp_messaging.verify_otp` | Validate OTP proof before completing sensitive setup. |
| `audit.record_event` | Record bootstrap, password, TOTP, user disable, and session security events. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `user.created` | User is created | Audit, Staff Access |
| `user.disabled` | User is disabled | Staff Access, session guards |
| `password.changed` | Password changes | Audit |
| `platform_owner.totp_enrolled` | Future TOTP support is enabled | Audit only in v1 |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `invalid_credentials` | Username/password/factor validation failed. |
| `first_password_change_required` | User cannot enter normal app until setup completes. |
| `otp_required` | Sensitive first-password setup needs OTP proof. |
| `totp_required` | Reserved for future PlatformApp hardening; not emitted by v1 PlatformApp login. |
| `wrong_app_scope` | User/session is valid but not for this app. |
