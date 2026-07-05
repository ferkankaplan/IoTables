# Access Context

Access owns human identity, authentication, app authorization, staff assignments, and OTP/TOTP security flows.

CustomerOrderingSession is not a human identity and belongs to Ordering.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [identity-access.md](identity-access.md) | Users, credentials, login sessions, first-login setup, platform owner TOTP |
| [staff-access.md](staff-access.md) | Staff profiles, roles, station assignment, hall assignment |
| [otp-messaging.md](otp-messaging.md) | OTP challenge lifecycle, verification, delivery attempts, SMS provider adapter |

## Contract Documents

| Contract | Purpose |
| --- | --- |
| [identity-access-contracts.md](identity-access-contracts.md) | User, credential, login session, first password, TOTP, and app-scope contracts |
| [staff-access-contracts.md](staff-access-contracts.md) | Staff role, station scope, hall scope, and permission guard contracts |
| [otp-messaging-contracts.md](otp-messaging-contracts.md) | OTP challenge, send, verify, and delivery state contracts |

## API Documents

| API Contract | Purpose |
| --- | --- |
| [identity-access-api.md](identity-access-api.md) | Login, first-password setup, password change, TOTP, session, and user endpoints |
| [staff-access-api.md](staff-access-api.md) | Staff profile, role, station assignment, and hall assignment endpoints |
| [otp-messaging-api.md](otp-messaging-api.md) | OTP challenge state, send, and verify endpoints |

## Policy Documents

| Document | Purpose |
| --- | --- |
| [permission-policy-matrix.md](permission-policy-matrix.md) | Current release source for who may call each module command/query and which scope checks are required |

## Primary Apps

- PlatformApp
- TenantApp
- CashierApp
- StationStaffApp
- ServiceStaffApp

## Boundary Rule

Access decides who the actor is and which app/scope they may use. Business transitions still belong to their domain modules.
