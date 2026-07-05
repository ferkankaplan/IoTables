# Module: Identity and Access

## Purpose

Identity and Access owns authentication, users, roles, first-login password setup, app access checks, and tenant scoping.

It decides who a person is, which tenant they belong to, which app they may enter, and which high-level role they have.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| User | Entity | create, read, disable |
| Credential | Security data | bootstrap, password change, invalidate |
| Role | Authorization concept | assign through Staff Access or platform rules |
| Login session | Session | create, refresh, revoke |
| First-login requirement | State | require and complete password setup |
| App access policy | Guard | allow/deny app entry |

## Not Owned

- Staff station/hall assignments, owned by Staff Access.
- OTP delivery, owned by OTP / Messaging.
- Tenant identity, owned by Platform / Tenant Registry.
- CustomerOrderingSession, owned by Customer Ordering.
- Business permissions inside payments, preparation, delivery, or ordering modules.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| PlatformApp / Platform Owner | platform login | Single-user platform scope in the current release |
| TenantApp / Tenant Admin | tenant admin login | Own tenant only |
| CashierApp / Cashier | cashier login | Own tenant and cashier role |
| StationStaffApp / Station Staff | station login | Own tenant and station role |
| ServiceStaffApp / Service Staff | service login | Own tenant and service role |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Authenticate user | Login to app | All authenticated apps |
| Require app role | Guard routes/actions | App backends |
| Create bootstrap user | Provision tenant admin/starter staff or tenant-created staff | Provisioning, TenantApp |
| Force first password change | Complete bootstrap credential setup | Tenant/staff apps |
| Disable user | Remove access | TenantApp |

## Internal Rules

- Bootstrap password is temporary.
- Bootstrap credentials must not allow continued access without first password change.
- Platform Owner is a platform-scoped user with `tenantId = null` and role `platform_owner`.
- The first Platform Owner must be created by an explicit one-time bootstrap command, not automatically on every server startup.
- PlatformApp login uses username/password only in the current release.
- Tenant admin first password setup requires OTP.
- Cashier first password setup requires OTP to tenant GSM during bootstrap.
- Station and service staff first password setup does not require OTP in the current release.
- Users can access only their tenant unless explicitly platform scoped.
- Current release password policy: minimum 12 characters for user-chosen passwords, reject known bootstrap/default passwords, and store only strong password hashes.
- Tenant admin and cashier use OTP only for first password setup in the current release.

## Operational Safety

- Password change must invalidate bootstrap credential state atomically.
- Login/session creation must be rate-limited and audited where needed.
- Authentication must never trust tenant or role data from the frontend.
- Disabled users cannot keep using old sessions.
- First-login state transitions must be idempotent.
- The app-scope and session portion of the current release permission policy is defined in [permission-policy-matrix.md](permission-policy-matrix.md).

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| User | bootstrap/active -> disabled | tenant nullable for platform owner, username, status, firstPasswordChangeRequired | Username unique within tenant/platform scope; tenant users cannot access PlatformApp; disabled users cannot keep using old sessions | Disable instead of hard-delete when audit, orders, payments, or transitions reference the user |
| Credential | bootstrap -> changed -> rotated | user, passwordHash, bootstrapCredential, changedAt | Plaintext passwords are never stored; bootstrap credentials cannot grant continued access after first login | Preserve credential metadata needed for audit; never preserve raw secrets |
| LoginSession | active -> expired/revoked | user, tenant, app scope, session token hash, issuedAt, expiresAt, revokedAt | Session tenant/app scope must match requested app; revoked/expired sessions fail closed | Expire/revoke; retain only safe metadata as needed |
| PlatformRoleAssignment | active -> disabled | user, role, status | Only `tenantId = null` users can hold `platform_owner`; current release allows exactly one active Platform Owner | Preserve role assignment history for platform audit |
| TotpFactor | enrolled -> enabled -> disabled/rotated | user, secretCiphertext, enrolledAt, enabled | Reserved for future PlatformApp security hardening; not required by current release PlatformApp login | Disable/rotate instead of deleting if audit needs evidence |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Platform owner login |
| TenantApp | Tenant admin login and staff user management |
| CashierApp | Cashier login |
| StationStaffApp | Station staff login |
| ServiceStaffApp | Service staff login |

## Future Service Boundary

- Own data: users, credentials, sessions, login state.
- Own APIs: authenticate, logout, require role, create bootstrap user.
- Published events: user.created, user.disabled, password.changed.
- Consumed events: tenant.created, tenant.suspended.
- Must not leak: password hashes, OTP values, session secrets.

## Open Questions

None currently.
